"""
System Tests for AI Interview Coach Platform.
End-to-end workflow tests that verify multi-step operations
across multiple API endpoints working together.
"""
import os
import json
import tempfile
import sqlite3
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────
# Fixtures: same isolated storage pattern as integration tests
# ──────────────────────────────────────────────
@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    """Redirect storage to temp directories."""
    users_file = str(tmp_path / "users.json")
    db_file = str(tmp_path / "database.db")
    stats_dir = str(tmp_path)

    with open(users_file, "w") as f:
        json.dump([], f)

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
        yield {"users_file": users_file, "db_file": db_file, "stats_dir": stats_dir}


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


# ──────────────────────────────────────────────
# System Test 1: Full auth lifecycle
# ──────────────────────────────────────────────
class TestFullAuthLifecycle:
    def test_register_then_login_then_me(self, client):
        """Register → Login → GET /me → all data consistent."""
        # 1. Register
        reg = client.post("/api/auth/register", json={
            "name": "Alice",
            "email": "alice@test.com",
            "password": "SecureP@ss1"
        })
        assert reg.status_code == 200
        reg_data = reg.json()
        assert reg_data["user"]["name"] == "Alice"
        reg_token = reg_data["access_token"]

        # 2. Login with same credentials
        login = client.post("/api/auth/login", json={
            "email": "alice@test.com",
            "password": "SecureP@ss1"
        })
        assert login.status_code == 200
        login_token = login.json()["access_token"]

        # 3. GET /me with the login token
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
        assert me.status_code == 200
        me_data = me.json()
        assert me_data["name"] == "Alice"
        assert me_data["email"] == "alice@test.com"

        # 4. Also verify registration token works
        me2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {reg_token}"})
        assert me2.status_code == 200
        assert me2.json()["email"] == "alice@test.com"


# ──────────────────────────────────────────────
# System Test 2: Session persistence flow
# ──────────────────────────────────────────────
class TestSessionPersistenceFlow:
    def test_register_save_session_fetch_stats(self, client, isolated_storage):
        """Register → Save sessions → GET /stats → verify data appears."""
        # 1. Register user
        reg = client.post("/api/auth/register", json={
            "name": "Bob",
            "email": "bob@test.com",
            "password": "SecureP@ss1"
        })
        assert reg.status_code == 200
        token = reg.json()["access_token"]
        user_id = reg.json()["user"]["id"]

        # 2. Insert multiple sessions directly (simulating completed sessions)
        conn = sqlite3.connect(isolated_storage["db_file"])
        sessions = [
            (user_id, "2025-01-10 09:00", "Interview", 75, 60, 80, 85),
            (user_id, "2025-01-11 10:00", "Debate", 82, 70, 85, 90),
            (user_id, "2025-01-12 11:00", "Intro", 90, 80, 95, 88),
        ]
        for s in sessions:
            conn.execute('''
                INSERT INTO sessions (user_id, date, mode, confidence_score, logic_rating, eye_contact_rating, posture_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', s)
        conn.commit()
        conn.close()

        # 3. Fetch dashboard stats
        resp = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()

        # 4. Verify aggregated data
        assert data["total_sessions"] == 3
        assert data["latest_score"] == 90  # last session's confidence_score
        assert data["latest_mode"] == "Intro"
        assert data["sessions_by_mode"]["Interview"] == 1
        assert data["sessions_by_mode"]["Debate"] == 1
        assert data["sessions_by_mode"]["Intro"] == 1
        assert data["avg_score"] > 0
        assert len(data["history"]) == 3
        assert len(data["radar"]) == 5

    def test_multi_user_isolation(self, client, isolated_storage):
        """Two users see only their own sessions."""
        # Register two users
        r1 = client.post("/api/auth/register", json={
            "name": "User1", "email": "u1@test.com", "password": "SecureP@ss1"
        })
        r2 = client.post("/api/auth/register", json={
            "name": "User2", "email": "u2@test.com", "password": "SecureP@ss1"
        })
        t1 = r1.json()["access_token"]
        t2 = r2.json()["access_token"]
        uid1 = r1.json()["user"]["id"]
        uid2 = r2.json()["user"]["id"]

        # Seed sessions for user1 only
        conn = sqlite3.connect(isolated_storage["db_file"])
        conn.execute('''
            INSERT INTO sessions (user_id, date, mode, confidence_score, logic_rating, eye_contact_rating, posture_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid1, "2025-01-01 09:00", "Interview", 80, 70, 85, 90))
        conn.commit()
        conn.close()

        # User1 should see 1 session
        s1 = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {t1}"}).json()
        assert s1["total_sessions"] == 1

        # User2 should see 0 sessions
        s2 = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {t2}"}).json()
        assert s2["total_sessions"] == 0


# ──────────────────────────────────────────────
# System Test 3: Error resilience
# ──────────────────────────────────────────────
class TestErrorResilience:
    def test_expired_token(self, client):
        """Manually crafted expired token should return 401."""
        import jwt
        from app.api.routes_auth import SECRET_KEY, ALGORITHM
        from datetime import datetime, timedelta, timezone

        expired_payload = {
            "user_id": 999,
            "email": "expired@test.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

    def test_malformed_json_body(self, client):
        """Sending malformed JSON body should return 422."""
        resp = client.post(
            "/api/auth/register",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 422

    def test_missing_required_fields(self, client):
        """Register without required fields returns 422."""
        resp = client.post("/api/auth/register", json={"name": "Incomplete"})
        assert resp.status_code == 422

    def test_root_always_available(self, client):
        """Health check endpoint should always return 200."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    def test_nonexistent_route_returns_404(self, client):
        """Unknown routes return 404."""
        resp = client.get("/api/nonexistent/route")
        assert resp.status_code == 404
