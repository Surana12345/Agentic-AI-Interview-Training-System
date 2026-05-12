"""
Shared evaluation service – extracts the duplicated posture scoring,
observation generation, and report-building logic used by all three modes
(Intro, Debate, Interview).
"""

import json
from typing import Optional


def compute_posture_scores(posture_data: dict) -> dict:
    """
    Given raw posture frame-counter stats, compute percentage scores
    for posture and eye contact.

    Returns:
        {
            "posture_pct": int,   # 0-100
            "eye_contact_pct": int,  # 0-100
            "posture_eye_avg": float
        }
    """
    total_frames = posture_data.get("totalFrames", 1)
    if total_frames <= 0:
        total_frames = 1

    good_posture = posture_data.get("goodPostureFrames", 0)
    good_eye = posture_data.get("goodEyeContactFrames", 0)

    posture_pct = int((good_posture / total_frames) * 100)
    eye_contact_pct = int((good_eye / total_frames) * 100)
    posture_eye_avg = (posture_pct + eye_contact_pct) / 2

    return {
        "posture_pct": posture_pct,
        "eye_contact_pct": eye_contact_pct,
        "posture_eye_avg": posture_eye_avg,
    }


def compute_confidence_score(logic_avg: float, posture_eye_avg: float) -> int:
    """
    70% weight to content quality (logic_avg), 30% to posture/eye contact.
    Clamped to 0-100.
    """
    score = int((logic_avg * 0.7) + (posture_eye_avg * 0.3))
    return max(0, min(100, score))


def build_posture_observations(posture_data: dict) -> str:
    """
    Generate a human-readable observations string based on raw posture counters.
    """
    observations = []
    if posture_data.get("slouched", 0) > 3:
        observations.append("Slouching detected.")
    if posture_data.get("lookedAway", 0) > 3:
        observations.append("Lack of eye contact detected.")
    if posture_data.get("fidgetCount", 0) > 3:
        observations.append("Excessive fidgeting/movement.")
    if posture_data.get("phoneDetected", 0) > 0:
        observations.append("Mobile phone usage detected in frame.")

    return " | ".join(observations) if observations else "Good overall posture."


def build_posture_agent(posture_pct: int, observations: str) -> dict:
    """Build the posture_agent section for the evaluation report."""
    return {
        "score": posture_pct,
        "status": _score_status(posture_pct),
        "ai_observations": observations,
    }


def build_eye_contact_agent(eye_contact_pct: int, observations: str) -> dict:
    """Build the eye_contact_agent section for the evaluation report."""
    return {
        "score": eye_contact_pct,
        "status": _score_status(eye_contact_pct),
        "ai_observations": observations,
    }


def build_emotion_agent(emotion: str) -> dict:
    """Build the emotion_agent section for the evaluation report."""
    return {
        "primary_emotion": emotion.capitalize(),
        "status": "Positive" if emotion in ["happy", "neutral", "surprised"] else "Nervous/Stressed"
    }


def _score_status(score: int) -> str:
    """Convert a 0-100 score to a status label."""
    if score >= 70:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


def extract_logic_avg(history: list) -> float:
    """
    Compute average logic_score from User entries in chat history.
    """
    vals = []
    for entry in history:
        if entry.get("role") == "User":
            try:
                vals.append(float(entry.get("logic_score", 0)))
            except (ValueError, TypeError):
                pass
    return sum(vals) / len(vals) if vals else 0


def extract_speech_metrics(history: list) -> dict:
    """
    Aggregate WPM, fillers, and fluency from User entries in chat history.
    """
    wpms = []
    fillers = []
    fluencies = []
    relevances = []
    
    for entry in history:
        if entry.get("role") == "User":
            wpms.append(float(entry.get("wpm", 0)))
            fillers.append(float(entry.get("fillers", 0)))
            fluencies.append(float(entry.get("fluency", 0)))
            if "semantic_relevance" in entry:
                relevances.append(float(entry.get("semantic_relevance", 0)))
                
    return {
        "wpm": int(sum(wpms) / len(wpms)) if wpms else 130,
        "fillers": int(sum(fillers) / len(fillers)) if fillers else 0,
        "fluency": int(sum(fluencies) / len(fluencies)) if fluencies else 85,
        "relevance": int(sum(relevances) / len(relevances)) if relevances else 0
    }


def extract_emotion(history: list) -> str:
    """
    Get the most frequent emotion from the chat history.
    """
    emotions = []
    for entry in history:
        if entry.get("role") == "User" and "emotion" in entry:
            emotions.append(entry["emotion"])
    
    if not emotions:
        return "neutral"
        
    return max(set(emotions), key=emotions.count)


def build_transcript(history: list) -> str:
    """
    Convert chat history into a readable transcript string.
    """
    lines = [
        f"{entry.get('role', '')}: {entry.get('text', '')}"
        for entry in history
    ]
    return "\n".join(lines)


def parse_posture_json(posture_stats: str) -> dict:
    """Safely parse posture stats JSON string, returning empty dict on failure."""
    try:
        return json.loads(posture_stats)
    except (json.JSONDecodeError, TypeError):
        return {}


def parse_llm_json(raw_text: str) -> dict:
    """
    Robustly extract JSON from LLM output that may contain markdown
    code fences or surrounding text.
    """
    clean = raw_text.replace("```json", "").replace("```", "").strip()
    json_start = clean.find("{")
    json_end = clean.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        return json.loads(clean[json_start:json_end])
    raise ValueError(f"No valid JSON found in LLM response: {raw_text[:200]}")


def build_session_report_data(
    confidence_score: int,
    logic_avg: float,
    eye_contact_pct: int,
    posture_pct: int,
    semantic_relevance: int = 0
) -> dict:
    """Build the standardised dict passed to save_session_to_db."""
    return {
        "confidence_score": confidence_score,
        "logic_rating": int(logic_avg),
        "eye_contact_rating": eye_contact_pct,
        "posture_rating": posture_pct,
        "semantic_relevance": semantic_relevance,
    }


def default_error_report(error_msg: str = "") -> dict:
    """Return a safe fallback report when processing fails."""
    improve = ["An error occurred while analyzing the session."]
    if error_msg:
        improve.append(error_msg)
    return {
        "overall_score": 0,
        "speech_agent": {"wpm": 0, "fillers": 0, "fluency": 0, "emotion": "N/A"},
        "content_agent": {
            "grammar": 0, "relevance": 0, "tone": "Error",
            "vocabulary_score": 0, "structure_score": 0,
            "keyword_coverage": 0, "readability_grade": 0,
            "word_count": 0, "advanced_words_found": [],
            "star_elements_found": [], "star_elements_missing": [],
        },
        "posture_agent": {"score": 0, "status": "Poor"},
        "emotion_agent": {"primary_emotion": "Unknown", "status": "Poor"},
        "feedback_good": [],
        "feedback_improve": improve,
    }
