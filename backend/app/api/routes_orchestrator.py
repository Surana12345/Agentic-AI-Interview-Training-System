import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.api.routes_auth import get_current_user
from app.agents.orchestrator_agent import run_orchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

class OrchestratorRequest(BaseModel):
    prompt: str

@router.post("/request")
async def handle_smart_start(req: OrchestratorRequest, current_user: dict = Depends(get_current_user)):
    """
    Handles unstructured user prompts from the Smart Start Dashboard banner,
    figures out what mode they want, and returns routing instructions.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    try:
        decision = run_orchestrator(req.prompt)
        return {
            "status": "success",
            "data": decision
        }
    except Exception as e:
        logger.error(f"Error in orchestrator route: {e}")
        raise HTTPException(status_code=500, detail="Failed to orchestrate request.")
