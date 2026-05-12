import os
import logging
from typing import TypedDict, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from app.services.content_analysis_service import analyze_content_comprehensive

logger = logging.getLogger(__name__)


class IntroState(TypedDict):
    transcript: str
    # Outputs
    logic_score: int
    is_silence: bool
    result_obj: Any
    content_metrics: dict


class ContentAgentOutput(BaseModel):
    grammar: int
    relevance: int
    tone: str


class IntroEvaluation(BaseModel):
    overall_score: int = Field(description="Score from 0-100 based on structure, relevance, and impact of the introduction.")
    content_agent: ContentAgentOutput
    feedback_good: list[str]
    feedback_improve: list[str]


def get_llm():
    return ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"], temperature=0.7)


def evaluate_intro(state: IntroState):
    llm = get_llm()
    structured_llm = llm.with_structured_output(IntroEvaluation)
    transcript = state.get("transcript", "")
    
    # NEW: Run deterministic analysis first
    content_metrics = analyze_content_comprehensive(transcript, "", "intro")
    
    readability = content_metrics.get("readability", {})
    vocabulary = content_metrics.get("vocabulary", {})
    star = content_metrics.get("star_method", {})
    
    # Build metrics block for LLM grounding
    metrics_block = (
        f"\nDETERMINISTIC ANALYSIS (use these as scoring anchors):\n"
        f"  - Word Count: {content_metrics.get('word_count', 0)}\n"
        f"  - Readability: {readability.get('readability_score', 'N/A')}/100 "
        f"(Grade Level: {readability.get('grade_level', 'N/A')})\n"
        f"  - Vocabulary Richness: {vocabulary.get('vocab_score', 'N/A')}/100 "
        f"(Advanced words: {', '.join(vocabulary.get('advanced_words_found', [])) or 'None'})\n"
        f"  - STAR Method Elements: {', '.join(star.get('elements_found', [])) or 'None'} "
        f"({star.get('structure_score', 0)}/100)\n"
    )
    
    prompt = PromptTemplate.from_template(
        "You are an expert HR Interviewer. Evaluate this candidate's Self-Introduction.\n\n"
        "Candidate's Introduction: \"{transcript}\"\n"
        "{metrics_block}\n"
        "SCORING RULES:\n"
        "- `grammar` score should be ANCHORED to the readability score above. "
        "If readability is 40, grammar must not exceed 60.\n"
        "- `relevance` should grade how well-structured and impactful the introduction is. Do NOT give 0 unless they speak complete nonsense. Even a brief intro should score at least 40 if it contains their name or background.\n"
        "- If vocabulary richness is low, suggest using more professional terminology.\n"
        "- If STAR elements are missing, mention this in feedback_improve.\n\n"
        "Provide structured feedback evaluating grammar, relevance, and tone.\n"
        "1. You MUST provide EXACTLY 4 `feedback_good` points and EXACTLY 4 `feedback_improve` points.\n"
        "2. BE ULTRA-CONCISE: Each point MUST be a single, short sentence (maximum 20-25 words). Do not write paragraphs.\n"
    )

    chain = prompt | structured_llm
    
    result = chain.invoke({
        "transcript": transcript,
        "metrics_block": metrics_block,
    })
    
    # BLEND grammar and relevance: 40% deterministic + 60% LLM
    det_readability = readability.get("readability_score", result.content_agent.grammar)
    blended_grammar = int(det_readability * 0.40 + result.content_agent.grammar * 0.60)
    blended_grammar = max(0, min(100, blended_grammar))
    
    # Update the result object's grammar with blended score
    result.content_agent.grammar = blended_grammar
    
    logger.info(
        "Intro content blending: grammar(LLM=%d, det=%d → blended=%d)",
        result.content_agent.grammar, det_readability, blended_grammar,
    )

    return {
        "logic_score": result.overall_score,
        "is_silence": False,
        "result_obj": result,
        "content_metrics": content_metrics,
    }


def build_intro_graph():
    graph = StateGraph(IntroState)
    graph.add_node("evaluate", evaluate_intro)
    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile()


intro_agent = build_intro_graph()


def run_intro_turn(state_input: Dict[str, Any]) -> Dict[str, Any]:
    return intro_agent.invoke(state_input)
