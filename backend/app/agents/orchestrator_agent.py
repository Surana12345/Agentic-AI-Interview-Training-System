import os
from typing import Literal, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Structured schema for the orchestrator response
class OrchestratorDecision(BaseModel):
    routed_module: Literal["interview", "debate", "intro", "general"] = Field(
        description="The appropriate module selected based on the user's request."
    )
    extracted_job_role: str = Field(
        default="",
        description="The job role extracted from the request (e.g., Software Engineer, Data Analyst)."
    )
    extracted_topic: str = Field(
        default="",
        description="The debate or discussion topic extracted from the request."
    )
    sys_reply: str = Field(
        description="A short conversational reply explaining what the system understood."
    )

# Create Gemini LLM instance
def get_orchestrator_llm():
    return ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL"],
        temperature=0.1  # Low temperature for more accurate routing
    )

# Main orchestration function
def run_orchestrator(user_prompt: str) -> Dict[str, Any]:
    llm = get_orchestrator_llm()

    # Convert Gemini output into structured format
    structured_llm = llm.with_structured_output(OrchestratorDecision)

    # Prompt used to route user requests
    system_prompt = PromptTemplate.from_template(
        "You are the Intelligent Orchestrator for the AI Interview Coach Platform.\n"
        "Your task is to understand the user's request and route it to the correct module.\n\n"
        "Available modules:\n"
        "1. interview → For role-specific HR or technical interviews.\n"
        "2. debate → For argument, discussion, or opinion-based sessions.\n"
        "3. intro → For self-introduction or elevator pitch practice.\n"
        "4. general → If the request does not clearly fit any module.\n\n"
        "User Request: \"{user_prompt}\"\n\n"
        "You must:\n"
        "- Select the correct module\n"
        "- Extract the job role if it is an interview request\n"
        "- Extract the topic if it is a debate request\n"
        "- Provide a short friendly response"
    )

    # Build chain
    chain = system_prompt | structured_llm

    try:
        # Invoke LLM
        result = chain.invoke({"user_prompt": user_prompt})

        # Return structured output
        return result.model_dump()

    except Exception as e:
        print(f"Orchestrator routing failed: {e}")

        # Fallback response if LLM fails
        return {
            "routed_module": "general",
            "extracted_job_role": "",
            "extracted_topic": "",
            "sys_reply": "I couldn't understand the request clearly. Please choose a mode manually."
        }
