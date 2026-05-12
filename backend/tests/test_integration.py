"""
Integration Tests for AI Interview Coach Platform.
Tests API routes via FastAPI TestClient with isolated temp storage.
No external server required – all tests are self-contained.
"""
import os
import json
import tempfile
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────
# Fixtures: isolated temp storage for users.json + database.db
# ──────────────────────────────────────────────
@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    """Redirect user storage and DB to temp directories for every test."""
    users_file = str(tmp_path / "users.json")
    db_file = str(tmp_path / "database.db")
    stats_dir = str(tmp_path)

    # Write an empty users file
    with open(users_file, "w") as f:
        json.dump([], f)

    # Create sessions table
    conn = sqlite3.connect(db_file)
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
    conn.close()

    with patch("app.api.routes_auth.USERS_FILE", users_file), \
         patch("app.api.routes_auth.STATS_DIR", stats_dir), \
         patch("app.api.routes_dashboard.DB_FILE", db_file), \
         patch("app.api.routes_dashboard.DATA_DIR", stats_dir):
        yield {"users_file": users_file, "db_file": db_file}


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def _register_user(client, name="Test User", email="test@example.com", password="StrongP@ss1"):
    return client.post("/api/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })


def _login_user(client, email="test@example.com", password="StrongP@ss1"):
    return client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────
# Auth route integration tests
# ──────────────────────────────────────────────
class TestAuthRoutes:
    def test_register_success(self, client):
        resp = _register_user(client)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        _register_user(client)
        resp = _register_user(client)
        assert resp.status_code == 409

    def test_register_invalid_email(self, client):
        resp = _register_user(client, email="not-an-email")
        assert resp.status_code == 400

    def test_register_weak_password(self, client):
        resp = _register_user(client, password="weak")
        assert resp.status_code == 400

    def test_login_success(self, client):
        _register_user(client)
        resp = _login_user(client)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        _register_user(client)
        resp = _login_user(client, password="WrongP@ss9")
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = _login_user(client, email="nobody@example.com")
        assert resp.status_code == 401

    def test_get_me_with_valid_token(self, client):
        reg = _register_user(client)
        token = reg.json()["access_token"]
        resp = client.get("/api/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_with_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers=_auth_header("invalid.token.here"))
        assert resp.status_code == 401

    def test_get_me_without_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code in [401, 403]


# ──────────────────────────────────────────────
# Dashboard route integration tests
# ──────────────────────────────────────────────
class TestDashboardRoutes:
    def test_stats_empty(self, client):
        reg = _register_user(client)
        token = reg.json()["access_token"]
        resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["history"] == []

    def test_stats_with_seeded_data(self, client, isolated_storage):
        reg = _register_user(client)
        token = reg.json()["access_token"]
        user_id = reg.json()["user"]["id"]

        # Seed a session directly into the DB
        conn = sqlite3.connect(isolated_storage["db_file"])
        conn.execute('''
            INSERT INTO sessions (user_id, date, mode, confidence_score, logic_rating, eye_contact_rating, posture_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, "2025-03-25 10:00", "Interview", 85, 70, 90, 80))
        conn.commit()
        conn.close()

        resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 1
        assert data["latest_score"] == 85
        assert data["latest_mode"] == "Interview"

    def test_stats_requires_auth(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code in [401, 403]


# ──────────────────────────────────────────────
# TTS route integration test
# ──────────────────────────────────────────────
class TestTTSRoute:
    def test_synthesize_empty_text(self, client):
        reg = _register_user(client)
        token = reg.json()["access_token"]
        resp = client.post(
            "/api/realtime/synthesize",
            json={"text": "", "lang": "en"},
        )
        # TTS endpoint doesn't require auth – just test the response
        data = resp.json()
        assert "error" in data

    def test_synthesize_valid_text(self, client):
        resp = client.post(
            "/api/realtime/synthesize",
            json={"text": "Hello world", "lang": "en"},
        )
        data = resp.json()
        # Either audio or error (depending on gTTS availability)
        assert "audio_base64" in data or "error" in data


# ──────────────────────────────────────────────
# Orchestrator route integration test (mocked agent)
# ──────────────────────────────────────────────
class TestOrchestratorRoute:
    @patch("app.api.routes_orchestrator.run_orchestrator")
    def test_orchestrator_success(self, mock_run, client):
        mock_run.return_value = {"mode": "interview", "confidence": 0.95}
        reg = _register_user(client)
        token = reg.json()["access_token"]
        resp = client.post(
            "/api/orchestrator/request",
            json={"prompt": "I want to practice interviews"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["mode"] == "interview"

    def test_orchestrator_requires_auth(self, client):
        resp = client.post(
            "/api/orchestrator/request",
            json={"prompt": "test"},
        )
        assert resp.status_code in [401, 403]


# ──────────────────────────────────────────────
# Root endpoint integration test
# ──────────────────────────────────────────────
class TestRootEndpoint:
    def test_health_check(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
