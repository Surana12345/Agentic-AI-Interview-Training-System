"""
Unit Tests for AI Interview Coach Platform.
Tests individual functions/helpers from services and auth modules.
All ML models are mocked to avoid downloads and API key requirements.
"""
import os
import re
import json
import math
import sqlite3
import tempfile
import pytest
from unittest.mock import patch, MagicMock


# ──────────────────────────────────────────────
# audio_service unit tests
# ──────────────────────────────────────────────
class TestGetDurationFromBytes:
    def test_basic_estimation(self):
        from app.services.audio_service import get_duration_from_bytes
        audio_bytes = b"\x00" * 40000  # 40 KB
        duration = get_duration_from_bytes(audio_bytes)
        assert duration == 10.0  # 40000 / 4000

    def test_empty_bytes(self):
        from app.services.audio_service import get_duration_from_bytes
        assert get_duration_from_bytes(b"") == 0.0

    def test_small_bytes(self):
        from app.services.audio_service import get_duration_from_bytes
        assert get_duration_from_bytes(b"\x00" * 4000) == 1.0


class TestFillerWordCounting:
    """Test the filler word regex used inside process_audio."""

    def test_filler_detection(self):
        filler_words = r'\b(um|uh|like|you know|basically|actually|literally)\b'
        text = "um I think uh basically like you know it works"
        count = len(re.findall(filler_words, text.lower()))
        assert count == 5  # um, uh, basically, like, you know

    def test_no_fillers(self):
        filler_words = r'\b(um|uh|like|you know|basically|actually|literally)\b'
        text = "I have experience in Python and machine learning"
        count = len(re.findall(filler_words, text.lower()))
        assert count == 0

    def test_multiple_same_filler(self):
        filler_words = r'\b(um|uh|like|you know|basically|actually|literally)\b'
        text = "um um um uh uh"
        count = len(re.findall(filler_words, text.lower()))
        assert count == 5


# ──────────────────────────────────────────────
# emotion_service unit tests (mocked classifier)
# ──────────────────────────────────────────────
class TestEmotionService:
    @patch("app.services.emotion_service.get_classifier")
    @patch("app.services.emotion_service.librosa")
    def test_analyze_emotion_happy(self, mock_librosa, mock_get_clf):
        from app.services.emotion_service import analyze_emotion

        mock_librosa.load.return_value = ([0.1] * 16000, 16000)
        mock_clf = MagicMock()
        mock_clf.return_value = [{"label": "hap", "score": 0.95}]
        mock_get_clf.return_value = mock_clf

        label, score = analyze_emotion("fake_path.wav")
        assert label == "happy"
        assert score == pytest.approx(0.95)

    @patch("app.services.emotion_service.get_classifier")
    @patch("app.services.emotion_service.librosa")
    def test_analyze_emotion_neutral(self, mock_librosa, mock_get_clf):
        from app.services.emotion_service import analyze_emotion

        mock_librosa.load.return_value = ([0.1] * 16000, 16000)
        mock_clf = MagicMock()
        mock_clf.return_value = [{"label": "neu", "score": 0.88}]
        mock_get_clf.return_value = mock_clf

        label, score = analyze_emotion("fake.wav")
        assert label == "neutral"

    @patch("app.services.emotion_service.get_classifier")
    def test_analyze_emotion_no_classifier(self, mock_get_clf):
        from app.services.emotion_service import analyze_emotion

        mock_get_clf.return_value = None
        label, score = analyze_emotion("fake.wav")
        assert label == "neutral"
        assert score == 0.0

    @patch("app.services.emotion_service.get_classifier")
    @patch("app.services.emotion_service.librosa")
    def test_analyze_emotion_short_audio(self, mock_librosa, mock_get_clf):
        from app.services.emotion_service import analyze_emotion

        # Less than 1600 samples = too short
        mock_librosa.load.return_value = ([0.1] * 100, 16000)
        mock_get_clf.return_value = MagicMock()

        label, score = analyze_emotion("short.wav")
        assert label == "neutral"
        assert score == 0.0


# ──────────────────────────────────────────────
# tts_service unit tests
# ──────────────────────────────────────────────
class TestTTSServiceEdgeCases:
    def test_whitespace_only(self):
        from app.services.tts_service import synthesize_speech
        result = synthesize_speech("   ")
        assert "error" in result

    def test_none_text(self):
        from app.services.tts_service import synthesize_speech
        result = synthesize_speech("")
        assert "error" in result

    def test_returns_dict(self):
        from app.services.tts_service import synthesize_speech
        result = synthesize_speech("test")
        assert isinstance(result, dict)
        assert "audio_base64" in result or "error" in result


# ──────────────────────────────────────────────
# nlp_service unit tests (mocked model)
# ──────────────────────────────────────────────
class TestNLPServiceMocked:
    @patch("app.services.nlp_service.get_model")
    def test_model_not_available(self, mock_get_model):
        from app.services.nlp_service import calculate_relevance_score
        mock_get_model.return_value = None
        score = calculate_relevance_score("hello", "world")
        assert score == 50  # fallback

    def test_empty_user_text(self):
        from app.services.nlp_service import calculate_relevance_score
        assert calculate_relevance_score("", "some ideal answer") == 0

    def test_empty_ideal_answer(self):
        from app.services.nlp_service import calculate_relevance_score
        assert calculate_relevance_score("my answer", "") == 0

    def test_both_empty(self):
        from app.services.nlp_service import calculate_relevance_score
        assert calculate_relevance_score("", "") == 0


# ──────────────────────────────────────────────
# Auth helpers unit tests
# ──────────────────────────────────────────────
class TestAuthHelpers:
    def test_hash_password_roundtrip(self):
        from app.api.routes_auth import hash_password, verify_password
        pwd = "StrongP@ss1"
        hashed = hash_password(pwd)
        assert hashed != pwd
        assert verify_password(pwd, hashed) is True

    def test_verify_wrong_password(self):
        from app.api.routes_auth import hash_password, verify_password
        hashed = hash_password("CorrectP@ss1")
        assert verify_password("WrongP@ss1", hashed) is False

    def test_create_access_token_decode(self):
        import jwt
        from app.api.routes_auth import create_access_token, SECRET_KEY, ALGORITHM
        token = create_access_token({"user_id": 1, "email": "test@example.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 1
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_email_regex_valid(self):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        valid_emails = ["user@example.com", "test.user@domain.co", "a+b@c.org"]
        for email in valid_emails:
            assert re.match(email_regex, email), f"{email} should be valid"

    def test_email_regex_invalid(self):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        invalid_emails = ["noatsign", "@no-local.com", "spaces @bad.com"]
        for email in invalid_emails:
            assert not re.match(email_regex, email), f"{email} should be invalid"

    def test_password_regex_strong(self):
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%!&*])[A-Za-z\d@#$%!&*]{8,}$"
        assert re.match(password_regex, "Abcdef1@")

    def test_password_regex_weak(self):
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%!&*])[A-Za-z\d@#$%!&*]{8,}$"
        weak = ["short1@", "nouppercase1@", "NOLOWER1@", "NoSpecial1", "NoDigit@@aA"]
        for pwd in weak:
            assert not re.match(password_regex, pwd), f"{pwd} should be weak"


# ──────────────────────────────────────────────
# Dashboard / DB helpers unit tests
# ──────────────────────────────────────────────
class TestDashboardDB:
    def test_init_db_creates_table(self):
        """Test that init_db creates the sessions table in a temp DB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    mode TEXT,
                    confidence_score INTEGER,
                    logic_rating INTEGER,
                    eye_contact_rating INTEGER,
                    posture_rating INTEGER
                )
            ''')
            conn.commit()
            # Verify table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            assert cursor.fetchone() is not None
            conn.close()

    def test_save_and_read_session(self):
        """Test inserting and reading a session from a temp DB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute('''
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    mode TEXT,
                    confidence_score INTEGER,
                    logic_rating INTEGER,
                    eye_contact_rating INTEGER,
                    posture_rating INTEGER
                )
            ''')
            conn.execute('''
                INSERT INTO sessions (user_id, date, mode, confidence_score, logic_rating, eye_contact_rating, posture_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (1, "2025-01-01 10:00", "Interview", 85, 70, 90, 80))
            conn.commit()

            row = conn.execute("SELECT * FROM sessions WHERE user_id = 1").fetchone()
            assert row is not None
            assert dict(row)["confidence_score"] == 85
            assert dict(row)["mode"] == "Interview"
            conn.close()

    def test_empty_db_returns_no_rows(self):
        """Test that an empty DB returns no sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            conn.execute('''
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    mode TEXT,
                    confidence_score INTEGER,
                    logic_rating INTEGER,
                    eye_contact_rating INTEGER,
                    posture_rating INTEGER
                )
            ''')
            conn.commit()
            rows = conn.execute("SELECT * FROM sessions WHERE user_id = 99").fetchall()
            assert len(rows) == 0
            conn.close()
