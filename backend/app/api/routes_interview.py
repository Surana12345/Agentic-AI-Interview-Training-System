import random
import json
import os
import logging
import pandas as pd
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from app.api.routes_dashboard import save_session_to_db
from app.agents.interview_agent import run_interview_turn
from app.dependencies import get_current_user
from app.services.evaluation_service import (
    parse_posture_json,
    parse_llm_json,
    compute_posture_scores,
    compute_confidence_score,
    build_posture_observations,
    build_posture_agent,
    build_eye_contact_agent,
    extract_logic_avg,
    build_transcript,
    build_session_report_data,
    default_error_report,
    extract_speech_metrics,
    extract_emotion,
    build_emotion_agent,
)
from app.services.audio_service import process_audio
from app.services.nlp_service import calculate_relevance_score

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────
class StartInterviewRequest(BaseModel):
    job_role: str = "Software Engineer"
    difficulty: str = "Medium"


class InterviewReplyResponse(BaseModel):
    user_transcript: str
    logic_score: int
    next_question: str
    is_silence: bool = False

class SpeechAgentOutput(BaseModel):
    wpm: int
    fillers: int
    fluency: int

class ContentAgentOutput(BaseModel):
    grammar: int
    relevance: int
    tone: str

class FeedbackReport(BaseModel):
    overall_score: int
    speech_agent: SpeechAgentOutput
    content_agent: ContentAgentOutput
    feedback_good: List[str]
    feedback_improve: List[str]



# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def get_csv_data(role: str, difficulty: str) -> Optional[dict]:
    try:
        filename = f"{role.lower().replace(' ', '_')}.csv"
        file_path = os.path.join("data", "questions", filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path).fillna('')
            filtered = df[df['difficulty'].str.lower() == difficulty.lower()]
            if not filtered.empty:
                return random.choice(filtered.to_dict('records'))
        return None
    except Exception:
        return None


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@router.post("/start")
async def start_interview(request: StartInterviewRequest, current_user: dict = Depends(get_current_user)):
    try:
        role = request.job_role
        diff = request.difficulty

        data = get_csv_data(role, diff)

        q_text = data['question_text'] if data else "Tell me about yourself."
        keywords = data['expected_keywords'] if data else ""
        summary = data['ideal_answer_summary'] if data else ""

        llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"])
        prompt_template = PromptTemplate.from_template(
            "Act as an HR Interviewer. Greet the candidate for the {role} role and ask: '{q_text}'. Keep it under 3 sentences."
        )
        chain = prompt_template | llm
        response = chain.invoke({"role": role, "q_text": q_text})

        return {
            "question": q_text,
            "expected_keywords": keywords,
            "ideal_answer_summary": summary,
            "ai_greeting": response.content.strip() if response.content else f"Let's start. {q_text}"
        }
    except Exception as e:
        logger.error("Interview start error: %s", e)
        # Fallback question if Gemini fails
        q_text = "Tell me about your professional background and why you are interested in this role."
        return {
            "question": q_text,
            "expected_keywords": "experience, skills, background",
            "ideal_answer_summary": "Candidate should summarize their career and motivation.",
            "ai_greeting": f"Welcome to the interview. Let's start with the first question: {q_text}"
        }


@router.post("/reply")
async def interview_reply(
    audio_file: UploadFile = File(...),
    current_question: str = Form(...),
    chat_history: str = Form("[]"),
    expected_keywords: str = Form(""),
    ideal_answer_summary: str = Form(""),
    turn_number: int = Form(1),
    job_role: str = Form("Software Engineer"),
    current_user: dict = Depends(get_current_user)
):
    try:
        audio_bytes = await audio_file.read()
        
        # 1. Real Audio Processing Pipeline (Whisper STT)
        audio_data = await asyncio.to_thread(process_audio, audio_bytes)
        transcript = audio_data.get("user_transcript", "[No speech detected]")
        
        state_input = {
            "job_role": job_role,
            "current_question": current_question,
            "expected_keywords": expected_keywords,
            "ideal_answer_summary": ideal_answer_summary,
            "chat_history": chat_history,
            "transcript": transcript,
            "turn_number": turn_number
        }
        
        # 2. Run LLM Agent and SentenceTransformers Model CONCURRENTLY
        if ideal_answer_summary and transcript not in ["[No speech detected]", "[Audio Error]"]:
            task_agent = asyncio.to_thread(run_interview_turn, state_input)
            task_nlp = asyncio.to_thread(calculate_relevance_score, transcript, ideal_answer_summary)
            
            agent_result, semantic_score = await asyncio.gather(task_agent, task_nlp)
            
            data = {
                "user_transcript": transcript,
                # Blend Gemini logic score (structure) with Semantic score (factual)
                "logic_score": int((agent_result.get("logic_score", 0) * 0.5) + (semantic_score * 0.5)),
                "semantic_relevance": semantic_score,
                "next_question": agent_result.get("next_question", ""),
                "is_silence": agent_result.get("is_silence", False)
            }
        else:
            agent_result = await asyncio.to_thread(run_interview_turn, state_input)
            data = {
                "user_transcript": transcript,
                "logic_score": agent_result.get("logic_score", 0),
                "next_question": agent_result.get("next_question", ""),
                "is_silence": agent_result.get("is_silence", False)
            }

        data["emotion"] = audio_data.get("emotion", "neutral")
        data["wpm"] = audio_data.get("wpm", 0)
        data["fillers"] = audio_data.get("fillers", 0)
        data["fluency"] = audio_data.get("fluency", 0)

        if data.get("is_silence") or data.get("user_transcript", "") in ["[No speech detected]", "[Audio Error]"]:
            data.update({
                "logic_score": 0,
                "user_transcript": "[No speech detected]",
                "next_question": f"I didn't catch that. Could you try again? {current_question}",
                "is_silence": True,
                "wpm": 0, "fillers": 0, "fluency": 0
            })

        return data
    except Exception as e:
        logger.error("Interview reply error: %s", e)
        return {"user_transcript": "[Audio Error]", "logic_score": 0, "next_question": current_question, "is_silence": True}


@router.post("/report")
async def generate_report(
    chat_history: str = Form(...),
    posture_stats: str = Form("{}"),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    try:
        from app.agents.evaluation_orchestrator import evaluation_orchestrator
        history = json.loads(chat_history)
        
        state_input = {
            "chat_history": history,
            "posture_stats_str": posture_stats,
            "mode": "interview"
        }
        
        final_state = await evaluation_orchestrator.ainvoke(state_input)
        data = final_state.get("final_report", {})
        
        report_data = build_session_report_data(
            confidence_score=data.get("overall_score", 0),
            logic_avg=final_state.get("logic_avg", 0.0),
            eye_contact_pct=final_state.get("scores", {}).get("eye_contact_pct", 85),
            posture_pct=final_state.get("scores", {}).get("posture_pct", 85),
        )
        save_session_to_db("Interview", report_data, user_id=user_id)
        
        return data
    except Exception as e:
        logger.error("Interview report error: %s", e)
        return default_error_report(str(e))