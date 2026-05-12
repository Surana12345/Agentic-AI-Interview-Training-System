import base64
import io
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

def synthesize_speech(text: str) -> dict:
    """
    Synthesize text to speech using gTTS and return base64 encoded MP3.
    """
    if not text:
        return {"error": "No text provided"}

    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Write audio to a bytes buffer
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Encode bytes to base64
        audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "mime_type": "audio/mp3"
        }
    except Exception as e:
        logger.error(f"TTS Synthesis failed: {str(e)}")
        return {"error": f"Synthesis failed: {str(e)}"}
