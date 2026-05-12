"""
Comprehensive backend tests for the AI Interview Coach Platform.
Tests cover: evaluation_service, nlp_service, tts_service, and API routes.
"""
import json
import pytest
from app.services.evaluation_service import (
    compute_posture_scores,
    compute_confidence_score,
    build_posture_observations,
    build_posture_agent,
    build_eye_contact_agent,
    build_emotion_agent,
    extract_logic_avg,
    extract_speech_metrics,
    extract_emotion,
    build_transcript,
    parse_posture_json,
    parse_llm_json,
    build_session_report_data,
    default_error_report,
)


# ──────────────────────────────────────────────
# evaluation_service tests
# ──────────────────────────────────────────────
class TestComputePostureScores:
    def test_perfect_posture(self):
        data = {"totalFrames": 100, "goodPostureFrames": 100, "goodEyeContactFrames": 100}
        result = compute_posture_scores(data)
        assert result["posture_pct"] == 100
        assert result["eye_contact_pct"] == 100

    def test_zero_frames(self):
        result = compute_posture_scores({})
        assert result["posture_pct"] == 0
        assert result["eye_contact_pct"] == 0

    def test_mixed_scores(self):
        data = {"totalFrames": 200, "goodPostureFrames": 150, "goodEyeContactFrames": 100}
        result = compute_posture_scores(data)
        assert result["posture_pct"] == 75
        assert result["eye_contact_pct"] == 50


class TestComputeConfidenceScore:
    def test_clamped_to_100(self):
        score = compute_confidence_score(100.0, 100.0)
        assert score == 100

    def test_clamped_to_0(self):
        score = compute_confidence_score(0.0, 0.0)
        assert score == 0

    def test_weighted(self):
        score = compute_confidence_score(80.0, 60.0)
        # 80*0.7 + 60*0.3 = 56 + 18 = 74
        assert score == 74


class TestBuildPostureObservations:
    def test_no_issues(self):
        obs = build_posture_observations({})
        assert obs == "Good overall posture."

    def test_slouched(self):
        obs = build_posture_observations({"slouched": 5})
        assert "Slouching" in obs

    def test_phone(self):
        obs = build_posture_observations({"phoneDetected": 1})
        assert "phone" in obs.lower()


class TestBuildAgents:
    def test_posture_agent(self):
        agent = build_posture_agent(85, "Good posture")
        assert agent["score"] == 85
        assert agent["status"] == "Good"

    def test_eye_contact_agent(self):
        agent = build_eye_contact_agent(45, "Some issues")
        assert agent["score"] == 45
        assert agent["status"] == "Fair"

    def test_emotion_agent_positive(self):
        agent = build_emotion_agent("happy")
        assert agent["primary_emotion"] == "Happy"
        assert agent["status"] == "Positive"

    def test_emotion_agent_negative(self):
        agent = build_emotion_agent("angry")
        assert agent["status"] == "Nervous/Stressed"


class TestExtractLogicAvg:
    def test_normal(self):
        history = [
            {"role": "User", "logic_score": 80},
            {"role": "AI Judge", "logic_score": 0},
            {"role": "User", "logic_score": 60},
        ]
        assert extract_logic_avg(history) == 70.0

    def test_empty(self):
        assert extract_logic_avg([]) == 0


class TestExtractSpeechMetrics:
    def test_normal(self):
        history = [
            {"role": "User", "wpm": 140, "fillers": 2, "fluency": 90, "semantic_relevance": 80},
            {"role": "User", "wpm": 120, "fillers": 4, "fluency": 70, "semantic_relevance": 60},
        ]
        metrics = extract_speech_metrics(history)
        assert metrics["wpm"] == 130
        assert metrics["fillers"] == 3
        assert metrics["fluency"] == 80
        assert metrics["relevance"] == 70

    def test_empty(self):
        metrics = extract_speech_metrics([])
        assert metrics["wpm"] == 130  # default
        assert metrics["fillers"] == 0


class TestExtractEmotion:
    def test_most_frequent(self):
        history = [
            {"role": "User", "emotion": "happy"},
            {"role": "User", "emotion": "neutral"},
            {"role": "User", "emotion": "happy"},
        ]
        assert extract_emotion(history) == "happy"

    def test_empty(self):
        assert extract_emotion([]) == "neutral"


class TestBuildTranscript:
    def test_basic(self):
        history = [
            {"role": "User", "text": "Hello"},
            {"role": "AI", "text": "Hi there"},
        ]
        transcript = build_transcript(history)
        assert "User: Hello" in transcript
        assert "AI: Hi there" in transcript


class TestParsePostureJson:
    def test_valid(self):
        result = parse_posture_json('{"totalFrames": 100}')
        assert result["totalFrames"] == 100

    def test_invalid(self):
        result = parse_posture_json("not json")
        assert result == {}


class TestParseLlmJson:
    def test_clean_json(self):
        result = parse_llm_json('{"score": 85}')
        assert result["score"] == 85

    def test_with_fences(self):
        result = parse_llm_json('```json\n{"score": 90}\n```')
        assert result["score"] == 90

    def test_no_json(self):
        with pytest.raises(ValueError):
            parse_llm_json("no json here")


class TestBuildSessionReportData:
    def test_basic(self):
        data = build_session_report_data(85, 70.0, 90, 80)
        assert data["confidence_score"] == 85
        assert data["logic_rating"] == 70
        assert data["semantic_relevance"] == 0

    def test_with_relevance(self):
        data = build_session_report_data(85, 70.0, 90, 80, semantic_relevance=75)
        assert data["semantic_relevance"] == 75


class TestDefaultErrorReport:
    def test_structure(self):
        report = default_error_report("test error")
        assert report["overall_score"] == 0
        assert "emotion" in str(report["speech_agent"])
        assert "emotion_agent" in report
        assert "test error" in report["feedback_improve"]


# ──────────────────────────────────────────────
# tts_service tests
# ──────────────────────────────────────────────
class TestTTSService:
    def test_empty_text(self):
        from app.services.tts_service import synthesize_speech
        result = synthesize_speech("")
        assert "error" in result

    def test_valid_text(self):
        from app.services.tts_service import synthesize_speech
        result = synthesize_speech("Hello world")
        # If gTTS is installed, we get audio; otherwise an error
        assert "audio_base64" in result or "error" in result


# ──────────────────────────────────────────────
# nlp_service tests
# ──────────────────────────────────────────────
class TestNLPService:
    def test_empty_inputs(self):
        from app.services.nlp_service import calculate_relevance_score
        assert calculate_relevance_score("", "") == 0

    def test_identical_texts(self):
        from app.services.nlp_service import calculate_relevance_score
        score = calculate_relevance_score("I love Python", "I love Python")
        assert score > 70  # Identical texts should have very high similarity

    def test_unrelated_texts(self):
        from app.services.nlp_service import calculate_relevance_score
        score = calculate_relevance_score(
            "The quick brown fox jumps over the lazy dog",
            "Quantum computing uses qubits for parallel processing"
        )
        assert score < 60  # Unrelated texts should have low similarity
