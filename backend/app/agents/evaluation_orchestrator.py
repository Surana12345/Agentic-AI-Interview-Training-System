import json
import os
import logging
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Re-use existing deterministic logic
from app.services.evaluation_service import (
    extract_speech_metrics,
    extract_emotion,
    build_posture_agent,
    build_eye_contact_agent,
    parse_posture_json,
    extract_logic_avg,
    compute_posture_scores,
    compute_confidence_score,
    build_transcript,
    build_posture_observations,
    build_emotion_agent
)

# NEW: Deterministic content analysis
from app.services.content_analysis_service import (
    analyze_content_comprehensive,
    extract_all_keywords,
    extract_user_transcript,
)

# Output Schemas for the LLM
class ContentAgentOutput(BaseModel):
    grammar: int = Field(description="Grammar score from 0 to 100, where 100 is perfect grammar.")
    relevance: int = Field(description="Content relevance score from 0 to 100, where 100 is perfectly relevant.")
    tone: str = Field(description="The overall tone, e.g. professional, casual, nervous, confident.")

class FeedbackReportOutput(BaseModel):
    content_agent: ContentAgentOutput
    feedback_good: List[str]
    feedback_improve: List[str]

# 1. State Definition
class EvaluationState(TypedDict, total=False):
    # Inputs
    chat_history: list
    posture_stats_str: str
    mode: str  # "interview" or "debate"
    
    # Internal Setup Data
    transcript: str
    user_only_transcript: str
    logic_avg: float
    scores: dict
    observations: list
    content_metrics: dict           # NEW: deterministic content analysis results
    all_expected_keywords: str      # NEW: aggregated keywords from session
    
    # Parallel Node Outputs
    speech_agent: dict
    emotion_agent: dict
    posture_agent: dict
    eye_contact_agent: dict
    content_agent: dict
    feedback_good: list
    feedback_improve: list
    
    # Final Synthesis Output
    overall_score: int
    final_report: dict

# 2. Setup Node — now includes deterministic content analysis
async def setup_node(state: EvaluationState) -> dict:
    history = state.get("chat_history", [])
    posture_str = state.get("posture_stats_str", "{}")
    mode = state.get("mode", "interview")
    
    posture = parse_posture_json(posture_str)
    logic_avg = extract_logic_avg(history)
    scores = compute_posture_scores(posture)
    transcript = build_transcript(history)
    observations = build_posture_observations(posture)
    
    # NEW: Extract user-only text and run deterministic content analysis
    user_transcript = extract_user_transcript(history)
    all_keywords = extract_all_keywords(history)
    content_metrics = analyze_content_comprehensive(user_transcript, all_keywords, mode)
    
    logger.info(
        "Content metrics computed: readability=%s, vocab=%s, keywords=%s, star=%s, composite=%s",
        content_metrics["readability"]["readability_score"],
        content_metrics["vocabulary"]["vocab_score"],
        content_metrics["keywords"]["keyword_score"],
        content_metrics["star_method"]["structure_score"],
        content_metrics["deterministic_content_score"],
    )
    
    return {
        "transcript": transcript,
        "user_only_transcript": user_transcript,
        "logic_avg": logic_avg,
        "scores": scores,
        "observations": observations,
        "content_metrics": content_metrics,
        "all_expected_keywords": all_keywords,
    }

# 3. Parallel Worker Nodes
async def speech_node(state: EvaluationState) -> dict:
    history = state.get("chat_history", [])
    speech_stats = extract_speech_metrics(history)
    dom_emotion = extract_emotion(history)
    
    return {
        "speech_agent": {
            "wpm": speech_stats["wpm"],
            "fillers": speech_stats["fillers"],
            "fluency": speech_stats["fluency"]
        },
        "emotion_agent": build_emotion_agent(dom_emotion)
    }

async def posture_node(state: EvaluationState) -> dict:
    scores = state.get("scores", {})
    observations = state.get("observations", [])
    
    p_agent = build_posture_agent(scores.get("posture_pct", 85), observations)
    e_agent = build_eye_contact_agent(scores.get("eye_contact_pct", 85), observations)
    
    return {
        "posture_agent": p_agent,
        "eye_contact_agent": e_agent
    }

async def content_node(state: EvaluationState) -> dict:
    mode = state.get("mode", "interview")
    transcript = state.get("transcript", "")
    logic_avg = state.get("logic_avg", 0.0)
    content_metrics = state.get("content_metrics", {})
    
    # Extract deterministic scores for the prompt
    readability = content_metrics.get("readability", {})
    vocabulary = content_metrics.get("vocabulary", {})
    keywords = content_metrics.get("keywords", {})
    star = content_metrics.get("star_method", {})
    word_count = content_metrics.get("word_count", 0)
    
    llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"], temperature=0.7)
    structured_llm = llm.with_structured_output(FeedbackReportOutput)
    
    coach_type = "interview coach" if mode == "interview" else "debate coach"
    
    # Build deterministic evidence block to anchor the LLM
    metrics_block = (
        f"DETERMINISTIC ANALYSIS (verified metrics — use these as anchors):\n"
        f"  - Word Count: {word_count}\n"
        f"  - Readability Score: {readability.get('readability_score', 'N/A')}/100 "
        f"(Flesch: {readability.get('flesch_raw', 'N/A')}, Grade: {readability.get('grade_level', 'N/A')})\n"
        f"  - Avg Sentence Length: {readability.get('avg_sentence_length', 'N/A')} words\n"
        f"  - Vocabulary Richness: {vocabulary.get('vocab_score', 'N/A')}/100 "
        f"(TTR: {vocabulary.get('ttr', 'N/A')}, Avg Word Length: {vocabulary.get('avg_word_length', 'N/A')})\n"
        f"  - Advanced Words Used: {', '.join(vocabulary.get('advanced_words_found', [])) or 'None'}\n"
        f"  - Keyword Coverage: {keywords.get('keyword_score', 'N/A')}/100 "
        f"({keywords.get('coverage_pct', 0)}% of expected keywords matched)\n"
        f"  - Keywords Missed: {', '.join(keywords.get('missed', [])) or 'None'}\n"
    )
    
    if mode in ("interview", "intro"):
        metrics_block += (
            f"  - STAR Method: {', '.join(star.get('elements_found', [])) or 'None'} "
            f"found | Missing: {', '.join(star.get('elements_missing', [])) or 'None'} "
            f"({star.get('structure_score', 0)}/100)\n"
        )
    
    relevance_instruction = ""
    if keywords.get("total_keywords", 0) > 0:
        relevance_instruction = (
            "   - Your `relevance` score should consider keyword coverage. If keyword coverage is 30%, "
            "relevance should NOT exceed 60. If coverage is 80%+, relevance can be 75-95.\n"
        )
    else:
        relevance_instruction = "   - Judge `relevance` entirely based on how well the candidate answered the core premise contextually without rigid keyword limits.\n"

    prompt = PromptTemplate.from_template(
        f"You are an elite, highly analytical {{coach_type}}. Your objective is to provide a rigorous, "
        f"highly specific assessment of the candidate's cognitive performance, domain knowledge, "
        f"and conversational structure.\n\n"
        "Session Transcript:\n{transcript}\n\n"
        "Metrics:\n- Avg Turn-by-Turn Logic Score: {logic_avg}%\n\n"
        "{metrics_block}\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. STRICT: Do NOT evaluate or mention audio quality, speech speed, fillers, or body language. "
        "Focus entirely on CONTENT.\n"
        "2. Grade their factual accuracy, argument framing, problem-solving structure, and technical depth.\n"
        "3. SCORING RANGE: `grammar` and `relevance` MUST be integers from 0 to 100.\n"
        "   - Your `grammar` score should be ANCHORED BY the deterministic readability score above. "
        "If readability is 40, your grammar should not be above 60. If readability is 85, grammar can be 80-95.\n"
        f"{relevance_instruction}"
        "   - A typical average answer should score 50-70. Only give below 30 for truly terrible performance.\n"
        "4. Provide EXACTLY 3 `feedback_good` points and EXACTLY 3 `feedback_improve` points.\n"
        "5. BE ULTRA-CONCISE: Each point MUST be a single, short sentence (maximum 20-25 words). Do not write paragraphs.\n"
        "6. MANDATORY EVIDENCE: Very briefly integrate a short quote (2-4 words) to justify your point.\n"
        "7. If the STAR method analysis shows missing elements, mention this in feedback_improve.\n"
        "8. If advanced vocabulary is low, suggest using more sophisticated language.\n"
    )
    
    chain = prompt | structured_llm
    report_obj = await chain.ainvoke({
        "coach_type": coach_type,
        "transcript": transcript,
        "logic_avg": f"{logic_avg:.0f}",
        "metrics_block": metrics_block,
    })
    
    # ── BLENDED SCORING: 40% deterministic + 60% LLM ──
    llm_grammar = report_obj.content_agent.grammar
    llm_relevance = report_obj.content_agent.relevance
    
    det_readability = readability.get("readability_score", llm_grammar)
    det_keyword = keywords.get("keyword_score", 0)
    det_vocab = vocabulary.get("vocab_score", 0)
    
    blended_grammar = int(det_readability * 0.40 + llm_grammar * 0.60)
    
    # Relevance blending depends on whether we have keyword data
    if keywords.get("total_keywords", 0) > 0:
        blended_relevance = int(det_keyword * 0.30 + llm_relevance * 0.70)
    else:
        blended_relevance = llm_relevance  # No keywords to anchor, trust LLM
    
    blended_grammar = max(0, min(100, blended_grammar))
    blended_relevance = max(0, min(100, blended_relevance))
    
    logger.info(
        "Content blending: grammar(LLM=%d, det=%d → blended=%d) | relevance(LLM=%d, det_kw=%d → blended=%d)",
        llm_grammar, det_readability, blended_grammar,
        llm_relevance, det_keyword, blended_relevance,
    )
    
    # Build enriched content_agent with new metrics
    content_agent = {
        "grammar": blended_grammar,
        "relevance": blended_relevance,
        "tone": report_obj.content_agent.tone,
        # NEW fields
        "vocabulary_score": det_vocab,
        "structure_score": star.get("structure_score", 0),
        "keyword_coverage": keywords.get("coverage_pct", 0),
        "readability_grade": readability.get("grade_level", 0),
        "word_count": word_count,
        "advanced_words_found": vocabulary.get("advanced_words_found", []),
        "star_elements_found": star.get("elements_found", []),
        "star_elements_missing": star.get("elements_missing", []),
    }
    
    return {
        "content_agent": content_agent,
        "feedback_good": report_obj.feedback_good,
        "feedback_improve": report_obj.feedback_improve
    }

# 4. Synthesis Node
async def synthesis_node(state: EvaluationState) -> dict:
    logic_avg = state.get("logic_avg", 0.0)
    scores = state.get("scores", {})
    speech = state.get("speech_agent", {})
    content = state.get("content_agent", {})
    
    # Use blended grammar/relevance from content_node
    grammar = content.get("grammar", 0)
    relevance = content.get("relevance", 0)
    fluency = speech.get("fluency", 85)
    fillers = speech.get("fillers", 0)
    posture_pct = scores.get("posture_pct", 85)
    eye_contact_pct = scores.get("eye_contact_pct", 85)
    
    # NEW: Include vocabulary and structure in overall score
    vocab_score = content.get("vocabulary_score", 50)
    structure_score = content.get("structure_score", 50)
    
    overall = int(
        (int(grammar) * 0.12) +
        (int(relevance) * 0.18) +
        (float(logic_avg) * 0.15) +
        (float(fluency) * 0.12) +
        (float(posture_pct) * 0.12) +
        (float(eye_contact_pct) * 0.08) +
        (max(0, 100 - int(fillers) * 10) * 0.03) +
        (int(vocab_score) * 0.10) +      # NEW
        (int(structure_score) * 0.10)     # NEW
    )
    final_conf = max(0, min(100, overall))
    
    # Assemble master report JSON matching what the frontend expects
    master_report = {
        "overall_score": final_conf,
        "speech_agent": state.get("speech_agent", {}),
        "posture_agent": state.get("posture_agent", {}),
        "eye_contact_agent": state.get("eye_contact_agent", {}),
        "emotion_agent": state.get("emotion_agent", {}),
        "content_agent": content,
        "feedback_good": state.get("feedback_good", []),
        "feedback_improve": state.get("feedback_improve", [])
    }
    
    return {
        "overall_score": final_conf,
        "final_report": master_report
    }

# 5. Build LangGraph
workflow = StateGraph(EvaluationState)

workflow.add_node("setup_node", setup_node)
workflow.add_node("speech_node", speech_node)
workflow.add_node("posture_node", posture_node)
workflow.add_node("content_node", content_node)
workflow.add_node("synthesis_node", synthesis_node)

# Flow logic: START -> Setup -> Parallel Branches -> Synthesis -> END
workflow.add_edge(START, "setup_node")
workflow.add_edge("setup_node", "speech_node")
workflow.add_edge("setup_node", "posture_node")
workflow.add_edge("setup_node", "content_node")

workflow.add_edge("speech_node", "synthesis_node")
workflow.add_edge("posture_node", "synthesis_node")
workflow.add_edge("content_node", "synthesis_node")

workflow.add_edge("synthesis_node", END)

evaluation_orchestrator = workflow.compile()
