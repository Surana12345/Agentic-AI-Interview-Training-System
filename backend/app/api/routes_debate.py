import random
import json
import os
import logging
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from app.api.routes_dashboard import save_session_to_db
from app.agents.debate_agent import run_debate_turn
from app.dependencies import get_current_user
from app.services.evaluation_service import (
    parse_posture_json,
    parse_llm_json,
    compute_posture_scores,
    compute_confidence_score,
    build_posture_observations,
    build_posture_agent,
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


class TopicRequest(BaseModel):
    topic: str = ""

class SpeechAgentOutput(BaseModel):
    wpm: int
    fillers: int
    fluency: int

class ContentAgentOutput(BaseModel):
    grammar: int
    relevance: int
    tone: str

class DebateFeedbackReport(BaseModel):
    overall_score: int
    speech_agent: SpeechAgentOutput
    content_agent: ContentAgentOutput
    feedback_good: List[str]
    feedback_improve: List[str]

class TopicResponse(BaseModel):
    topic: str


@router.post("/start")
async def start_debate(request: TopicRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_topic = request.topic.strip()
        llm = ChatGoogleGenerativeAI(model=os.environ["GEMINI_MODEL"]).with_structured_output(TopicResponse)

        if not user_topic:
            target = random.choice([
                "AI Ethics", "Remote Work", "Cybersecurity", "Social Media",
                "Climate Change", "Education System", "Technology and Society",
                "Future of Work", "Globalization", "Privacy and Data Security"
            ])
            prompt = f"Generate ONE concise, single-line debate topic about {target}."
        else:
            prompt = f"Return the topic exactly as '{user_topic}'."

        response = llm.invoke(prompt)
        return {"topic": response.topic if response.topic else "Is AI beneficial?"}
    except Exception:
        return {"topic": user_topic if user_topic else "AI Ethics"}


@router.post("/reply")
async def debate_reply(
    audio_file: UploadFile = File(...),
    topic: str = Form(...),
    chat_history: str = Form("[]"),
    turn_number: int = Form(1),
    current_user: dict = Depends(get_current_user)
):
    try:
        audio_bytes = await audio_file.read()
        
        # 1. Real Audio Processing Pipeline (Whisper STT)
        audio_data = await asyncio.to_thread(process_audio, audio_bytes)
        transcript = audio_data.get("user_transcript", "[No speech detected]")
        
        state_input = {
            "topic": topic,
            "user_stance": "Unknown",
            "difficulty": "Medium",
            "chat_history": chat_history,
            "transcript": transcript,
            "turn_number": turn_number
        }
        
        # 2. Run LLM Agent and SentenceTransformers Model CONCURRENTLY
        if topic and transcript not in ["[No speech detected]", "[Audio Error]"]:
            task_agent = asyncio.to_thread(run_debate_turn, state_input)
            task_nlp = asyncio.to_thread(calculate_relevance_score, transcript, topic)
            
            agent_result, semantic_score = await asyncio.gather(task_agent, task_nlp)
            
            data = {
                "user_transcript": transcript,
                "logic_score": int((agent_result.get("logic_score", 0) * 0.5) + (semantic_score * 0.5)),
                "semantic_relevance": semantic_score,
                "ai_counter_argument": agent_result.get("ai_rebuttal", ""),
                "is_silence": agent_result.get("is_silence", False)
            }
        else:
            agent_result = await asyncio.to_thread(run_debate_turn, state_input)
            data = {
                "user_transcript": transcript,
                "logic_score": agent_result.get("logic_score", 0),
                "ai_counter_argument": agent_result.get("ai_rebuttal", ""),
                "is_silence": agent_result.get("is_silence", False)
            }

        data["emotion"] = audio_data.get("emotion", "neutral")
        data["wpm"] = audio_data.get("wpm", 0)
        data["fillers"] = audio_data.get("fillers", 0)
        data["fluency"] = audio_data.get("fluency", 0)

        # 3. Handle silence / no speech
        if data.get("is_silence") or transcript in ["[No speech detected]", "[Audio Error]"]:
            data.update({
                "logic_score": 0,
                "user_transcript": "[No speech detected]",
                "ai_counter_argument": f"I didn't catch that. Could you try again? The topic is: {topic}",
                "is_silence": True,
                "wpm": 0, "fillers": 0, "fluency": 0
            })

        return data
        
    except Exception as e:
        logger.error("Debate reply error: %s", e)
        raise HTTPException(status_code=500, detail="Rebuttal failed.")


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
            "mode": "debate"
        }
        
        final_state = await evaluation_orchestrator.ainvoke(state_input)
        data = final_state.get("final_report", {})
        
        report_data = build_session_report_data(
            confidence_score=data.get("overall_score", 0),
            logic_avg=final_state.get("logic_avg", 0.0),
            eye_contact_pct=final_state.get("scores", {}).get("eye_contact_pct", 85),
            posture_pct=final_state.get("scores", {}).get("posture_pct", 85),
        )
        save_session_to_db("Debate", report_data, user_id=user_id)
        
        return data
    except Exception as e:
        logger.error("Debate report error: %s", e)
        return default_error_report(str(e))