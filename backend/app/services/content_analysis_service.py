"""
Content Analysis Service — Deterministic content evaluation metrics.

Provides ground-truth scoring for grammar/readability, vocabulary richness,
keyword coverage, and STAR method structure detection. These metrics anchor
the LLM's subjective grading so it cannot inflate scores.
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False
    logger.warning("textstat not installed. Using heuristic readability. Install with: pip install textstat")


# ────────────────────────────────────────────────────────────────
# Advanced Vocabulary — words that signal professional communication
# ────────────────────────────────────────────────────────────────
ADVANCED_VOCABULARY = {
    # Professional connectors
    "furthermore", "consequently", "nevertheless", "moreover", "specifically",
    "subsequently", "additionally", "therefore", "however", "alternatively",
    # Technical & business terms
    "implementation", "optimization", "scalability", "architecture", "methodology",
    "infrastructure", "comprehensive", "systematically", "significantly",
    "efficiently", "effectively", "strategically", "analytically", "proactively",
    "leverage", "facilitate", "collaborate", "innovate", "prioritize",
    "framework", "paradigm", "benchmark", "stakeholder", "deliverable",
    "quantitative", "qualitative", "iterative", "agile", "robust",
    "deployed", "integrated", "automated", "streamlined", "orchestrated",
    # Action verbs for interviews
    "spearheaded", "established", "optimized", "architected", "mentored",
    "coordinated", "implemented", "developed", "designed", "analyzed",
    "resolved", "achieved", "improved", "reduced", "increased",
    "managed", "initiated", "transformed", "consolidated", "negotiated",
}


# ────────────────────────────────────────────────────────────────
# STAR Method Patterns
# ────────────────────────────────────────────────────────────────
STAR_PATTERNS = {
    "situation": [
        r"\b(situation|context|background|when i was|at my previous|in my role|"
        r"there was a time|one example|for instance|in my last|at my company|"
        r"during my|while working|i was working)\b"
    ],
    "task": [
        r"\b(task|responsibility|goal|objective|challenge|problem|assigned|"
        r"needed to|had to|was responsible|was tasked|my role was|"
        r"the requirement|what was needed|i was asked)\b"
    ],
    "action": [
        r"\b(i did|i implemented|i created|i designed|i built|i developed|"
        r"i led|i managed|i analyzed|steps i took|my approach|i decided|"
        r"i proposed|i organized|i solved|i wrote|i tested|i deployed|"
        r"what i did|the approach|i started by|first i|then i)\b"
    ],
    "result": [
        r"\b(result|outcome|impact|achieved|improved|reduced|increased|saved|"
        r"successfully|led to|as a result|this resulted|the outcome|ended up|"
        r"which meant|this helped|we were able|performance improved|"
        r"delivered|completed|accomplished)\b"
    ],
}


# ────────────────────────────────────────────────────────────────
# 1. Grammar & Readability Analysis
# ────────────────────────────────────────────────────────────────
def analyze_grammar_readability(text: str) -> dict:
    """
    Compute deterministic grammar and readability metrics.
    Uses textstat for Flesch reading ease / grade level.
    Falls back to heuristic if textstat is not installed.
    """
    if not text:
        return {
            "readability_score": 0, "flesch_raw": 0,
            "grade_level": 0, "sentence_count": 0, "avg_sentence_length": 0,
        }
    if len(text.split()) < 5:
        return {
            "readability_score": 90, "flesch_raw": 100,
            "grade_level": 1, "sentence_count": 1, "avg_sentence_length": len(text.split()),
        }

    if HAS_TEXTSTAT:
        flesch = textstat.flesch_reading_ease(text)
        grade = textstat.flesch_kincaid_grade(text)
        sentence_count = textstat.sentence_count(text)
        avg_sent_len = len(text.split()) / max(1, sentence_count)

        # Lenient normalization: Spoken language is usually simple. 
        # Flesch 50-80 is fine for spoken interviews.
        if 40 <= flesch <= 85:
            readability_norm = 85 + (15 * (1 - abs(flesch - 65) / 25))
        elif flesch > 85:
            readability_norm = max(60, 100 - (flesch - 85) * 1.2)
        else:
            readability_norm = max(45, flesch + 35)

        return {
            "readability_score": int(min(100, max(0, readability_norm))),
            "flesch_raw": round(flesch, 1),
            "grade_level": round(grade, 1),
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sent_len, 1),
        }
    else:
        # ── Heuristic fallback ──
        words = text.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_count = max(1, len(sentences))
        avg_sent_len = len(words) / sentence_count

        if 12 <= avg_sent_len <= 20:
            score = 75
        elif avg_sent_len < 8:
            score = 50
        elif avg_sent_len > 25:
            score = 55
        else:
            score = 65

        return {
            "readability_score": score,
            "flesch_raw": 0,
            "grade_level": 0,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sent_len, 1),
        }


# ────────────────────────────────────────────────────────────────
# 2. Vocabulary Richness
# ────────────────────────────────────────────────────────────────
def analyze_vocabulary_richness(text: str) -> dict:
    """
    Compute vocabulary richness:
      - Type-Token Ratio (TTR): unique words / total words
      - Average word length
      - Advanced vocabulary percentage
    """
    if not text or len(text.split()) < 5:
        return {
            "ttr": 0, "avg_word_length": 0, "advanced_vocab_pct": 0,
            "advanced_words_found": [], "vocab_score": 0,
        }

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return {
            "ttr": 0, "avg_word_length": 0, "advanced_vocab_pct": 0,
            "advanced_words_found": [], "vocab_score": 0,
        }

    total = len(words)
    unique = len(set(words))

    ttr = unique / total
    avg_word_len = sum(len(w) for w in words) / total
    advanced_found = sorted(set(w for w in words if w in ADVANCED_VOCABULARY))
    advanced_pct = (len(advanced_found) / total) * 100

    # Composite score - made lenient for spoken language
    ttr_score = min(100, ttr * 150)          # 0.66 → 100 (spoken language is repetitive)
    len_score = min(100, max(0, (avg_word_len - 3.5) * 35)) # 6.3 avg length → 100
    adv_score = min(100, advanced_pct * 25)  # 4% advanced words → 100 (10% was too strict)

    # Base minimum vocabulary score of 40 to avoid crushing confidence
    vocab_score = 40 + (int((ttr_score * 0.40) + (len_score * 0.30) + (adv_score * 0.30)) * 0.6)

    return {
        "ttr": round(ttr, 3),
        "avg_word_length": round(avg_word_len, 1),
        "advanced_vocab_pct": round(advanced_pct, 1),
        "advanced_words_found": advanced_found,
        "vocab_score": min(100, max(0, vocab_score)),
    }


# ────────────────────────────────────────────────────────────────
# 3. Keyword Coverage
# ────────────────────────────────────────────────────────────────
def analyze_keyword_coverage(text: str, expected_keywords: str) -> dict:
    """
    Check how many expected keywords / phrases the user mentioned.
    Returns coverage percentage and matched/missed lists.
    """
    if not text or not expected_keywords:
        return {
            "coverage_pct": 0, "matched": [], "missed": [],
            "total_keywords": 0, "keyword_score": 0,
        }

    text_lower = text.lower()
    keywords = [k.strip().lower() for k in re.split(r'[,;|]', expected_keywords) if k.strip()]
    if not keywords:
        return {
            "coverage_pct": 0, "matched": [], "missed": [],
            "total_keywords": 0, "keyword_score": 0,
        }

    matched, missed = [], []

    for kw in keywords:
        if kw in text_lower:
            matched.append(kw)
        else:
            # Partial match: if ≥60% of multi-word keyword's words appear
            kw_words = kw.split()
            if len(kw_words) > 1:
                hits = sum(1 for w in kw_words if w in text_lower)
                if hits >= len(kw_words) * 0.6:
                    matched.append(kw)
                else:
                    missed.append(kw)
            else:
                missed.append(kw)

    # Lenient coverage: matching ~65% of expected keywords gets a 100
    raw_coverage = (len(matched) / len(keywords)) * 100 if keywords else 0
    lenient_coverage = min(100, raw_coverage * 1.5)
    
    # Base 30 points if they spoke at all to avoid 0s
    keyword_score = 30 + (lenient_coverage * 0.7) if keywords else 0

    return {
        "coverage_pct": round(raw_coverage, 1),
        "matched": matched,
        "missed": missed,
        "total_keywords": len(keywords),
        "keyword_score": int(keyword_score),
    }


# ────────────────────────────────────────────────────────────────
# 4. STAR Method Detection
# ────────────────────────────────────────────────────────────────
def detect_star_method(text: str) -> dict:
    """
    Detect STAR framework elements (Situation, Task, Action, Result).
    Returns which elements were found and a structure score.
    """
    if not text or len(text.split()) < 10:
        return {
            "elements_found": [], "elements_missing": list(STAR_PATTERNS.keys()),
            "structure_score": 0, "has_complete_star": False,
        }

    text_lower = text.lower()
    found, missing = [], []

    for element, patterns in STAR_PATTERNS.items():
        element_found = any(re.search(p, text_lower) for p in patterns)
        (found if element_found else missing).append(element)

    # Lenient STAR scoring: finding 3 out of 4 elements gives 100%
    # finding 2 elements gives 70%
    score_map = {0: 30, 1: 50, 2: 70, 3: 100, 4: 100}

    return {
        "elements_found": found,
        "elements_missing": missing,
        "structure_score": score_map.get(len(found), 30),
        "has_complete_star": len(found) >= 3, # Consider 3/4 'complete enough'
    }


# ────────────────────────────────────────────────────────────────
# 5. Comprehensive Analysis (main entry point)
# ────────────────────────────────────────────────────────────────
def extract_all_keywords(history: list) -> str:
    """Aggregate expected_keywords from all User entries in chat history."""
    keywords = []
    for entry in history:
        if entry.get("role") == "User" and entry.get("expected_keywords"):
            keywords.append(entry["expected_keywords"])
    return ", ".join(keywords)


def extract_user_transcript(history: list) -> str:
    """Extract only the User's spoken text from chat history."""
    return " ".join(
        entry.get("text", "")
        for entry in history
        if entry.get("role") == "User"
    )


def analyze_content_comprehensive(
    transcript: str,
    expected_keywords: str = "",
    mode: str = "interview",
) -> dict:
    """
    Run ALL content analysis functions and return a unified report.
    This is the main entry point for deterministic content evaluation.
    """
    readability = analyze_grammar_readability(transcript)
    vocabulary = analyze_vocabulary_richness(transcript)
    keywords = analyze_keyword_coverage(transcript, expected_keywords)
    star = detect_star_method(transcript) if mode in ("interview", "intro") else {
        "structure_score": 0, "elements_found": [], "elements_missing": [], "has_complete_star": False
    }

    word_count = len(transcript.split()) if transcript else 0

    # ── Composite deterministic score (mode-aware weights) ──
    r = readability["readability_score"]
    v = vocabulary["vocab_score"]
    k = keywords["keyword_score"]
    s = star["structure_score"]

    if mode == "interview":
        deterministic = int(r * 0.25 + v * 0.20 + k * 0.30 + s * 0.25)
    elif mode == "debate":
        deterministic = int(r * 0.30 + v * 0.35 + k * 0.15 + s * 0.20)
    else:  # intro
        deterministic = int(r * 0.35 + v * 0.30 + k * 0.10 + s * 0.25)

    return {
        "word_count": word_count,
        "readability": readability,
        "vocabulary": vocabulary,
        "keywords": keywords,
        "star_method": star,
        "deterministic_content_score": min(100, max(0, deterministic)),
    }
