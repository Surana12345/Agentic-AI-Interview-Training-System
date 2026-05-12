import os
from typing import TypedDict, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

class DebateState(TypedDict):
    topic: str
    user_stance: str
    difficulty: str
    chat_history: str
    transcript: str
    turn_number: int
    # Outputs
    logic_score: int
    ai_rebuttal: str
    is_silence: bool

class DebateEvaluation(BaseModel):
    logic_score: int = Field(description="Score from 0-100 evaluating the strength of the user's argument.")
    ai_rebuttal: str = Field(description="The AI's counter-argument or exactly 'DEBATE_COMPLETE'.")

def get_llm():
    return ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"], temperature=0.7)

def evaluate_debate(state: DebateState):
    llm = get_llm()
    structured_llm = llm.with_structured_output(DebateEvaluation)
    
    turn_number = state.get("turn_number", 1)
    topic = state.get("topic", "")
    user_stance = state.get("user_stance", "")
    diff = state.get("difficulty", "Medium")

    next_step = (
        f"Generate a concise, challenging {diff} level rebuttal (under 3 sentences). "
        "Do NOT repeat previous points."
    ) if turn_number < 5 else "Set ai_rebuttal to exactly 'DEBATE_COMPLETE'."

    prompt = PromptTemplate.from_template(
        "You are an expert debater. First, determine the user's stance from their argument. Then, aggressively hold the OPPOSITE stance.\n\n"
        "Debate Topic: {topic}\n"
        "Difficulty: {difficulty}\n"
        "Conversation History: {chat_history}\n"
        "User's Latest Argument: \"{transcript}\"\n\n"
        "Instructions:\n"
        "1. Evaluate the logical strength of the user's argument (0-100).\n"
        "2. {next_step}\n"
    )

    chain = prompt | structured_llm
    
    result = chain.invoke({
        "topic": topic,
        "user_stance": user_stance,
        "difficulty": diff,
        "chat_history": state.get("chat_history", "[]"),
        "transcript": state.get("transcript", ""),
        "next_step": next_step
    })

    return {
        "logic_score": result.logic_score,
        "ai_rebuttal": result.ai_rebuttal,
        "is_silence": False
    }

def build_debate_graph():
    graph = StateGraph(DebateState)
    graph.add_node("evaluate", evaluate_debate)
    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", END)
    return graph.compile()

debate_agent = build_debate_graph()

def run_debate_turn(state_input: Dict[str, Any]) -> Dict[str, Any]:
    return debate_agent.invoke(state_input)
