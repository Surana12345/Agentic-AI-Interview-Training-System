from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ai_coach")

# 1. FORCE imports (No try/except)
from app.api import routes_intro, routes_debate, routes_interview, routes_dashboard, routes_auth, routes_orchestrator, routes_realtime

app = FastAPI(
    title="Agentic AI Coach API",
    description="AI-native interview coaching platform with LangGraph orchestration and MediaPipe computer vision.",
    version="1.0.0",
)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. FORCE router inclusion (No try/except)
app.include_router(routes_auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(routes_orchestrator.router, prefix="/api/orchestrator", tags=["Orchestrator"])
app.include_router(routes_intro.router, prefix="/api/intro", tags=["Intro"])
app.include_router(routes_debate.router, prefix="/api/debate", tags=["Debate"])
app.include_router(routes_interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(routes_dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(routes_realtime.router, prefix="/api/realtime", tags=["Realtime"])

@app.get("/")
def read_root():
    return {"status": "online", "message": "Backend is running!"}