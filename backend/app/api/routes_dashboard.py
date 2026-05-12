import sqlite3
import os
import statistics
from datetime import datetime
from fastapi import APIRouter, Query, Depends
from app.api.routes_auth import get_current_user

router = APIRouter()

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data"
)
DB_FILE = os.path.join(DATA_DIR, "database.db")

def get_db_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
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

# Initialize DB on module load
init_db()

def save_session_to_db(mode, report_data, user_id: int = None):
    conn = get_db_connection()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn.execute('''
        INSERT INTO sessions (user_id, date, mode, confidence_score, logic_rating, eye_contact_rating, posture_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        date_str,
        mode,
        report_data.get("confidence_score", 0),
        report_data.get("logic_rating", 0),
        report_data.get("eye_contact_rating", 0),
        report_data.get("posture_rating", 0)
    ))
    conn.commit()
    conn.close()

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY id ASC", (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    history = [dict(row) for row in rows]

    if not history:
        return {
            "history": [],
            "radar": [],
            "latest_score": 0,
            "latest_mode": "None",
            "total_sessions": 0,
            "sessions_by_mode": {"Intro": 0, "Debate": 0, "Interview": 0},
            "avg_score": 0
        }

    total = len(history)
    scores = [s.get("confidence_score", 0) for s in history]
    avg_conf = sum(scores) / total
    avg_logic = sum(s.get("logic_rating", 0) for s in history) / total
    avg_eye = sum(s.get("eye_contact_rating", 0) for s in history) / total
    avg_posture = sum(s.get("posture_rating", 0) for s in history) / total

    # Compute consistency score
    if len(scores) >= 2:
        recent_scores = scores[-10:]  # Last 10 sessions
        stddev = statistics.stdev(recent_scores)
        consistency = max(0, min(100, int(100 - (stddev * 1.5))))
    else:
        consistency = int(avg_conf)

    # Count sessions by mode
    sessions_by_mode = {"Intro": 0, "Debate": 0, "Interview": 0}
    for s in history:
        mode = s.get("mode", "")
        if mode in sessions_by_mode:
            sessions_by_mode[mode] += 1
        else:
            sessions_by_mode[mode] = 1

    # Latest session values for radar
    latest = history[-1]
    latest_conf = latest.get("confidence_score", 0)
    latest_logic = latest.get("logic_rating", 0)
    latest_eye = latest.get("eye_contact_rating", 0)
    latest_posture = latest.get("posture_rating", 0)

    radar_data = [
        {"subject": "Confidence", "avg": int(avg_conf), "latest": latest_conf, "fullMark": 100},
        {"subject": "Logic", "avg": int(avg_logic), "latest": latest_logic, "fullMark": 100},
        {"subject": "Posture", "avg": int(avg_posture), "latest": latest_posture, "fullMark": 100},
        {"subject": "Eye Contact", "avg": int(avg_eye), "latest": latest_eye, "fullMark": 100},
        {"subject": "Consistency", "avg": consistency, "latest": consistency, "fullMark": 100}
    ]

    line_data = [
        {
            "name": s["date"],
            "score": s["confidence_score"],
            "mode": s["mode"],
            "logic": s.get("logic_rating", 0),
            "eye": s.get("eye_contact_rating", 0),
            "posture": s.get("posture_rating", 0)
        }
        for s in history
    ]

    return {
        "history": line_data,
        "radar": radar_data,
        "latest_score": history[-1]["confidence_score"],
        "latest_mode": history[-1]["mode"],
        "total_sessions": total,
        "sessions_by_mode": sessions_by_mode,
        "avg_score": int(avg_conf)
    }