from transformers import pipeline
import logging
import torch
import librosa
import numpy as np

logger = logging.getLogger(__name__)

# 'harshitv804/wav2vec2-lg-xlsr-en-speech-emotion-recognition' is a robust model
# Using a slightly smaller or better-known model: 'superb/wav2vec2-base-superb-er'
emotion_classifier = None

def get_classifier():
    global emotion_classifier
    if emotion_classifier is None:
        try:
            emotion_classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")
        except Exception as e:
            logger.warning("Error loading Emotion Classifier: %s", e)
    return emotion_classifier

def analyze_emotion(audio_path):
    """
    Analyzes the emotion of an audio file.
    Returns the top emotion and its probability.
    """
    
    classifier = get_classifier()
    if not classifier:
        return "neutral", 0.0
    
    try:
        # Load audio with librosa (resample to 16kHz which is what wav2vec2 expects)
        speech, sr = librosa.load(audio_path, sr=16000)
        
        # Ensure it's not too long or too short
        if len(speech) < 1600: # less than 0.1s
            return "neutral", 0.0
        
        # Prediction
        results = classifier(speech)
        
        # Results is a list of dicts like [{'label': 'neu', 'score': 0.9}, ...]
        if results:
            top_result = results[0]
            # Map labels to human readable if needed
            label_map = {
                'neu': 'neutral',
                'hap': 'happy',
                'ang': 'angry',
                'sad': 'sad',
                'sur': 'surprised',
                'fea': 'fearful',
                'dis': 'disgusted'
            }
            label = label_map.get(top_result['label'], top_result['label'])
            return label, float(top_result['score'])
    except Exception as e:
        logger.error("Error in emotion analysis: %s", e)
    
    return "neutral", 0.0
