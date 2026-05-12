import logging

logger = logging.getLogger(__name__)

def calculate_relevance_score(user_text, ideal_answer):
    """
    Computes a simple word intersection relevance score.
    Returns a score from 0-100.
    """
    if not user_text or not ideal_answer:
        return 0
    try:
        user_words = set(user_text.lower().split())
        ideal_words = set(ideal_answer.lower().split())
        if not ideal_words:
            return 50
        intersection = user_words.intersection(ideal_words)
        score = (len(intersection) / len(ideal_words)) * 100
        return min(100, max(0, int(score)))
    except Exception as e:
        logger.error("Error in relevance calculation: %s", e)
        return 50
