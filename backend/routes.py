import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from typing import List, Dict, Any

try:
    import edge_tts
except ImportError:
    edge_tts = None

from models import LoginRequest, IncidentRequest, ApprovalRequest, TTSRequest
from database import run_query, init_db
from agent_engine import process_incident_stream, approve_incident_stream
from tools import trigger_soundbox_chime
from logger import log

router = APIRouter(prefix="/api")

# High-fidelity Microsoft Edge TTS voice mapping for top Indian languages
EDGE_TTS_VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "mr": "mr-IN-AarohiNeural",
    "gu": "gu-IN-DhwaniNeural",
    "bn": "bn-IN-TanishaaNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural",
    "kn": "kn-IN-SapnaNeural",
    "ml": "ml-IN-SobhanaNeural",
    "ur": "ur-IN-GulNeural"
}

_AUDIO_CACHE: Dict[str, bytes] = {}

@router.post("/admin/reset-demo")
def reset_demo():
    """Resets all 5 merchant scenarios back to initial stuck state for repeated presentations."""
    init_db(force_seed=True)
    return {"status": "SUCCESS", "message": "All 5 merchant scenarios reset to initial state"}

@router.post("/auth/login")
def login(req: LoginRequest):
    """Authenticates merchant by username and password."""
    merchants = run_query(
        "SELECT id, name, username, business_type, bank_name, account_number, ifsc, phone FROM merchants WHERE username = ? AND password = ? LIMIT 1",
        (req.username, req.password)
    )
    if not merchants:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"status": "SUCCESS", "merchant": merchants[0]}

@router.get("/merchants")
def list_merchants():
    """Returns the 5 demo merchants for the 1-click presentation quick-switcher."""
    merchants = run_query("SELECT id, name, username, password, business_type, bank_name FROM merchants ORDER BY id ASC")
    return {"merchants": merchants}

@router.get("/merchants/{merchant_id}/data")
def get_merchant_data(merchant_id: str):
    """Fetches live transactions, batches, and Soundbox status for the merchant dashboard."""
    merchants = run_query("SELECT * FROM merchants WHERE id = ? LIMIT 1", (merchant_id,))
    if not merchants:
        raise HTTPException(status_code=404, detail="Merchant not found")

    transactions = run_query("SELECT * FROM transactions WHERE merchant_id = ? ORDER BY id DESC LIMIT 5", (merchant_id,))
    batches = run_query("SELECT * FROM settlement_batches WHERE merchant_id = ? ORDER BY id DESC LIMIT 5", (merchant_id,))
    soundbox = run_query("SELECT * FROM soundbox_devices WHERE merchant_id = ? LIMIT 1", (merchant_id,))

    return {
        "merchant": merchants[0],
        "transactions": transactions,
        "settlement_batches": batches,
        "soundbox": soundbox[0] if soundbox else None
    }

@router.post("/incident/stream")
async def incident_stream(req: IncidentRequest):
    """Streams multi-agent incident resolution events as Server-Sent Events (SSE)."""
    log.info(f"[API:incident/stream] Received query from {req.merchant_id} ({req.language}): '{req.message}'")

    async def event_generator():
        for event in process_incident_stream(req.merchant_id, req.message, req.scenario_hint, req.language):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/incident/approve")
async def approve_incident(req: ApprovalRequest):
    """Resumes execution after a human supervisor approves a high-value settlement hold."""
    log.info(f"[API:incident/approve] Incident: {req.incident_id}, Approved: {req.approved}")

    async def event_generator():
        for event in approve_incident_stream(req.incident_id, req.approved, req.notes, req.language or "en"):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/soundbox/test-chime")
def test_soundbox_chime(device_id: str, amount: float = 60.0):
    """Direct test trigger for Soundbox audio chime."""
    result = trigger_soundbox_chime.invoke({"device_id": device_id, "amount": amount})
    return {"status": "SUCCESS", "message": result}

@router.post("/tts")
async def generate_speech(req: TTSRequest):
    """Synthesizes high-fidelity neural voiceover using Edge TTS in the selected Indian language."""
    if not edge_tts:
        raise HTTPException(
            status_code=503,
            detail="edge-tts is not installed. Please install it using 'pip install edge-tts' or use browser native voice."
        )

    lang = (req.language or "en").lower()
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    voice = EDGE_TTS_VOICES.get(lang, "en-IN-NeerjaNeural")
    cache_key = f"{voice}::{text}"
    if cache_key in _AUDIO_CACHE:
        log.info(f"[TTS] Serving cached audio for {lang} ({len(_AUDIO_CACHE[cache_key])} bytes)")
        return Response(content=_AUDIO_CACHE[cache_key], media_type="audio/mpeg")

    try:
        log.info(f"[TTS] Synthesizing speech with {voice} for: '{text[:40]}...'")
        communicate = edge_tts.Communicate(text, voice)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        
        audio_data = b"".join(chunks)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize audio")
        
        _AUDIO_CACHE[cache_key] = audio_data
        log.info(f"[TTS] Successfully generated {len(audio_data)} bytes of audio ({voice})")
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        log.error(f"[TTS] Edge TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


