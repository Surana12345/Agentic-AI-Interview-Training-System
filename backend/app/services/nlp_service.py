from sentence_transformers import SentenceTransformer, util
import logging
import torch

logger = logging.getLogger(__name__)

# Standard lightweight model for semantic similarity
# 'all-MiniLM-L6-v2' is ~80MB and very fast
model = None

def get_model():
    global model
    if model is None:
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning("Error loading SentenceTransformer: %s", e)
    return model

def calculate_relevance_score(user_text, ideal_answer):
    """
    Computes semantic similarity between user text and ideal answer.
    Returns a score from 0-100.
    """
    if not user_text or not ideal_answer:
        return 0
    
    nlp_model = get_model()
    if not nlp_model:
        return 50 # Fallback 
    
    try:
        # Compute embeddings
        embeddings1 = nlp_model.encode(user_text, convert_to_tensor=True)
        embeddings2 = nlp_model.encode(ideal_answer, convert_to_tensor=True)
        
        # Compute cosine similarity
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        score = float(cosine_scores[0][0])
        
        # Scale range a bit. Cosine sim is -1 to 1, but for text embeddings usually 0.3+
        # normalize 0.4-0.9 range to 0-100 logically
        normalized_score = max(0, min(100, int((score - 0.2) / 0.7 * 100)))
        return normalized_score
    except Exception as e:
        logger.error("Error in relevance calculation: %s", e)
        return 50
