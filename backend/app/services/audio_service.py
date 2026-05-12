import os
import io
import uuid
import re
import logging
from google import genai
from google.genai import types

try:
    from faster_whisper import WhisperModel
    import webrtcvad
    import pydub
    from app.services.emotion_service import analyze_emotion
    from app.services.nlp_service import calculate_relevance_score
    HAS_LOCAL_AUDIO_ML = True
except ImportError:
    HAS_LOCAL_AUDIO_ML = False

logger = logging.getLogger(__name__)

# Initialize Whisper Model (Lazy load to save memory)
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None and HAS_LOCAL_AUDIO_ML:
        try:
            # CPU is usually safe and enough for tiny/base models on most machines
            _whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        except Exception as e:
            logger.warning("Whisper init failed: %s", e)
    return _whisper_model

def get_duration_from_bytes(audio_bytes: bytes) -> float:
    """Fallback duration estimation based on WebM byte size (approx ~32kbps)"""
    # Just an estimation if ffmpeg is missing
    return len(audio_bytes) / 4000.0

def process_audio(audio_bytes: bytes, use_local_ml: bool = True):
    """
    Process audio bytes to extract transcript and speech metrics (WPM, fluency).
    Attempts to use Whisper and WebRTC VAD if available and ffmpeg is installed.
    Falls back to Gemini if local ML fails or is unavailable.
    """
    transcript = None
    wpm = 130
    fluency = 85
    fillers = 0
    emotion = "neutral"
    relevance_score = 0
    
    temp_file = f"temp_audio_{uuid.uuid4().hex}.webm"
    
    # Write file and immediately close handle
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
            

    # STT with Whisper
    # 1. Transcribe Audio via Gemini (MUCH Faster than CPU Whisper)
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"],
            contents=[
                "Transcribe this audio precisely. Do not add any extra text or formatting. Just the transcription.",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm")
            ]
        )
        transcript = response.text.strip() if response.text else "[No speech detected]"
    except Exception as e:
        logger.error("Gemini STT failed: %s", e)
        transcript = "[Audio Processing Error]"

    # 2. Extract Speech Metrics / Emotion
    if HAS_LOCAL_AUDIO_ML and transcript not in ["[No speech detected]", "[Audio Processing Error]"]:
        try:
            # Emotion Analysis
            emotion, _ = analyze_emotion(temp_file)
            
            # VAD with WebRTC
            audio = pydub.AudioSegment.from_file(temp_file)
            duration_sec = len(audio) / 1000.0
            
            audio = audio.set_frame_rate(16000).set_channels(1)
            vad = webrtcvad.Vad(2)
            
            frames = [audio.raw_data[i:i+320] for i in range(0, len(audio.raw_data), 320)]
            speech_frames = sum(1 for frame in frames if len(frame) == 320 and vad.is_speech(frame, 16000))
            speech_sec = (speech_frames * 20) / 1000.0
            
            word_count = len(transcript.split())
            wpm = int((word_count / speech_sec) * 60) if speech_sec > 0 else 0
            fluency = int(min(100, (speech_sec / duration_sec) * 100)) if duration_sec > 0 else 0
            
        except Exception as ml_err:
            logger.warning("Local Audio ML failed (ffmpeg missing?): %s", ml_err)
            dur = get_duration_from_bytes(audio_bytes)
            wpm = int((len(transcript.split()) / dur) * 60) if dur > 0 else 130
    else:
        if transcript not in ["[No speech detected]", "[Audio Processing Error]"]:
            dur = get_duration_from_bytes(audio_bytes)
            wpm = int((len(transcript.split()) / dur) * 60) if dur > 0 else 130

    # Count fillers via Regex
    if transcript not in ["[No speech detected]", "[Audio Processing Error]"]:
        filler_words = r'\b(um|uh|like|you know|basically|actually|literally)\b'
        fillers = len(re.findall(filler_words, transcript.lower()))

    # 3. Final cleanup
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception as e:
            logger.debug("Failed to remove temp file %s: %s", temp_file, e)

    return {
        "user_transcript": transcript,
        "wpm": max(0, min(300, wpm)), # Clamp to realistic values
        "fluency": max(0, min(100, fluency)),
        "fillers": fillers,
        "emotion": emotion
    }
