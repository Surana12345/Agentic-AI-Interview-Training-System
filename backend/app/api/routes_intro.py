import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from dotenv import load_dotenv

from app.api.routes_dashboard import save_session_to_db
from app.agents.intro_agent import run_intro_turn
from app.dependencies import get_current_user
from app.services.evaluation_service import (
    parse_posture_json,
    parse_llm_json,
    compute_posture_scores,
    build_posture_observations,
    build_posture_agent,
    build_eye_contact_agent,
    build_session_report_data,
    default_error_report,
    build_emotion_agent,
)
from app.services.audio_service import process_audio

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload-audio")
async def analyze_intro(
    audio_file: UploadFile = File(...),
    posture_data: str = Form('{"status": "No posture data provided"}'),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    try:
        audio_bytes = await audio_file.read()

        if len(audio_bytes) < 1000:
            raise Exception("The audio file is empty.")

        pos_data = parse_posture_json(posture_data)
        
        # 1. Process audio specifically for speech metrics
        audio_data = process_audio(audio_bytes)
        transcript = audio_data.get("user_transcript", "[No speech detected]")
        wpm = audio_data.get("wpm", 0)
        fluency = audio_data.get("fluency", 0)
        fillers = audio_data.get("fillers", 0)

        # ── Silence / no-speech detection ──
        is_silence = audio_data.get("is_silence", False) or transcript in ["[No speech detected]", "[Audio Error]", ""]
        
        if is_silence:
            pos_scores = compute_posture_scores(pos_data)
            observations = build_posture_observations(pos_data)
            zero_report = {
                "overall_score": 0,
                "content_agent": {"grammar": 0, "relevance": 0, "tone": "N/A"},
                "speech_agent": {"wpm": 0, "fillers": 0, "fluency": 0, "emotion": "neutral"},
                "posture_agent": build_posture_agent(pos_scores["posture_pct"], observations),
                "eye_contact_agent": build_eye_contact_agent(pos_scores["eye_contact_pct"], observations),
                "emotion_agent": build_emotion_agent("neutral"),
                "feedback_good": ["No speech was detected during this session."],
                "feedback_improve": [
                    "Please speak clearly into the microphone.",
                    "Ensure your microphone is not muted.",
                    "Try again with a longer, audible introduction."
                ],
            }
            report_data = build_session_report_data(
                confidence_score=0,
                logic_avg=0,
                eye_contact_pct=0,
                posture_pct=pos_scores["posture_pct"],
            )
            save_session_to_db("Intro", report_data, user_id=user_id)
            return zero_report

        agent_result = run_intro_turn({
            "transcript": transcript
        })
        
        evaluation = agent_result["result_obj"]
        content_metrics = agent_result.get("content_metrics", {})
        
        # Build content_agent with enriched metrics
        vocabulary = content_metrics.get("vocabulary", {})
        star = content_metrics.get("star_method", {})
        readability = content_metrics.get("readability", {})
        
        analysis_results = {
            "content_agent": {
                "grammar": evaluation.content_agent.grammar,
                "relevance": evaluation.content_agent.relevance,
                "tone": evaluation.content_agent.tone,
                # NEW enriched fields
                "vocabulary_score": vocabulary.get("vocab_score", 0),
                "structure_score": star.get("structure_score", 0),
                "keyword_coverage": 0,  # No keywords for intro mode
                "readability_grade": readability.get("grade_level", 0),
                "word_count": content_metrics.get("word_count", 0),
                "advanced_words_found": vocabulary.get("advanced_words_found", []),
                "star_elements_found": star.get("elements_found", []),
                "star_elements_missing": star.get("elements_missing", []),
            },
            "feedback_good": evaluation.feedback_good,
            "feedback_improve": evaluation.feedback_improve
        }
        
        # Merge deterministic audio stats into the result
        analysis_results["speech_agent"] = {
            "wpm": wpm,
            "fillers": fillers,
            "fluency": fluency,
            "emotion": audio_data.get("emotion", "neutral")
        }
        analysis_results["emotion_agent"] = build_emotion_agent(audio_data.get("emotion", "neutral"))
        
        analysis_results["wpm"] = wpm
        analysis_results["fillers"] = fillers
        analysis_results["fluency"] = fluency
        analysis_results["emotion"] = audio_data.get("emotion", "neutral")

        # Compute posture scores using shared service
        scores = compute_posture_scores(pos_data)
        observations = build_posture_observations(pos_data)

        analysis_results["posture_agent"] = build_posture_agent(
            scores["posture_pct"], observations
        )
        analysis_results["eye_contact_agent"] = build_eye_contact_agent(
            scores["eye_contact_pct"], observations
        )

        # ── DETERMINISTIC OVERALL SCORE (now includes vocab + structure) ──
        grammar = evaluation.content_agent.grammar
        relevance = evaluation.content_agent.relevance
        posture_pct = scores["posture_pct"]
        eye_contact_pct = scores["eye_contact_pct"]
        vocab_score = vocabulary.get("vocab_score", 50)
        structure_score = star.get("structure_score", 50)
        
        overall = int(
            (grammar * 0.15) +
            (relevance * 0.20) +
            (fluency * 0.15) +
            (posture_pct * 0.12) +
            (eye_contact_pct * 0.10) +
            (max(0, 100 - fillers * 10) * 0.03) +
            (vocab_score * 0.13) +           # NEW
            (structure_score * 0.12)          # NEW
        )
        analysis_results["overall_score"] = max(0, min(100, overall))

        # Save session
        report_data = build_session_report_data(
            confidence_score=analysis_results.get("overall_score", 0),
            logic_avg=analysis_results.get("content_agent", {}).get("relevance", 0),
            eye_contact_pct=scores["eye_contact_pct"],
            posture_pct=scores["posture_pct"],
        )
        save_session_to_db("Intro", report_data, user_id=user_id)

        return analysis_results

    except Exception as e:
        logger.error("Intro analysis error: %s", e)
        return default_error_report(str(e))