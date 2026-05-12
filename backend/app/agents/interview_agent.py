import os
from typing import TypedDict, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from app.services.llm_factory import get_llm_with_fallbacks

# Define State
class InterviewState(TypedDict):
    job_role: str
    current_question: str
    expected_keywords: str
    ideal_answer_summary: str
    chat_history: str
    transcript: str
    turn_number: int
    # Outputs
    logic_score: int
    next_question: str
    is_silence: bool

# Output Schema
class InterviewEvaluation(BaseModel):
    logic_score: int = Field(description="Score from 0 to 100 on answer relevance, depth, and keywords.")
    next_question: str = Field(description="The next follow-up question, or exactly 'INTERVIEW_COMPLETE'.")


def evaluate_and_generate(state: InterviewState):
    chain_with_fallbacks = get_llm_with_fallbacks(structured_output_schema=InterviewEvaluation)
    
    turn_number = state.get("turn_number", 1)
    job_role = state.get("job_role", "Software Engineer")
    next_step = (
        f"Generate ONE new follow-up interview question for a {job_role} candidate. "
        "The question MUST be different from all previous questions in the history. "
        "Do NOT repeat or rephrase any question already asked."
    ) if turn_number < 5 else "Set next_question to exactly 'INTERVIEW_COMPLETE'."

    prompt = PromptTemplate.from_template(
        "You are an expert HR interviewer evaluating a {job_role} candidate.\n\n"
        "Current Question: \"{current_question}\"\n"
        "Expected Keywords: {expected_keywords}\n"
        "Ideal Answer Summary: {ideal_answer_summary}\n"
        "Conversation History: {chat_history}\n"
        "Transcript of User's Answer: \"{transcript}\"\n\n"
        "Instructions:\n"
        "1. Evaluate Relevance (0-40), Depth (0-30), Keywords (0-30). Sum logic_score (0-100).\n"
        "2. {next_step}\n"
    )

    chain = prompt | chain_with_fallbacks
    
    result = chain.invoke({
        "job_role": job_role,
        "current_question": state.get("current_question", ""),
        "expected_keywords": state.get("expected_keywords", ""),
        "ideal_answer_summary": state.get("ideal_answer_summary", ""),
        "chat_history": state.get("chat_history", "[]"),
        "transcript": state.get("transcript", ""),
        "next_step": next_step
    })

    return {
        "logic_score": result.logic_score,
        "next_question": result.next_question,
        "is_silence": False
    }

# Build LangGraph
def build_interview_graph():
    graph = StateGraph(InterviewState)
    graph.add_node("evaluate", evaluate_and_generate)
    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile()

interview_agent = build_interview_graph()

def run_interview_turn(state_input: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to cleanly invoke the graph."""
    return interview_agent.invoke(state_input)
