from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.services.tts_service import synthesize_speech
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class TTSRequest(BaseModel):
    text: str

@router.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Endpoint for text-to-speech synthesis.
    """
    result = synthesize_speech(request.text)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.websocket("/ws/coaching")
async def websocket_coaching(websocket: WebSocket):
    """
    Placeholder for realtime coaching websocket.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, this would process frames or audio chunks
            await websocket.send_text(f"Processed: {data}")
    except WebSocketDisconnect:
        logger.info("Coaching WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
