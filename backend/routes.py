import json
import asyncio
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from typing import List, Dict, Any, Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

from models import LoginRequest, IncidentRequest, ApprovalRequest, TTSRequest, StegoGenerateRequest, StegoVerifyRequest, QRVoiceRequest
from database import run_query, init_db
from agent_engine import process_incident_stream, approve_incident_stream, process_qr_voice_query
from tools import trigger_soundbox_chime
from config import get_sarvam_client, SARVAM_STT_MODEL, SARVAM_TTS_MODEL
from logger import log
from stego_service import generate_stego_qr_template, verify_stego_qr_image, create_sample_tampered_image

router = APIRouter(prefix="/api")

# Sarvam language codes mapping for top 10 Indian languages
SARVAM_LANG_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN"
}

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
    "pa": "pa-IN-OjasNeural",
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

@router.post("/voice/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("hi")
):
    """Transcribes merchant spoken voice in regional Indian languages via Sarvam AI Saaras STT."""
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Invalid audio recording")

    client = get_sarvam_client()
    if not client:
        raise HTTPException(status_code=503, detail="Sarvam AI service not configured")

    lang_code = SARVAM_LANG_CODES.get(language.lower(), "hi-IN")
    filename = file.filename or "recording.webm"
    content_type = file.content_type or "audio/webm"

    try:
        log.info(f"[STT] Transcribing voice input with Sarvam AI ({lang_code}, {len(audio_bytes)} bytes)")
        res = client.speech_to_text.transcribe(
            file=(filename, audio_bytes, content_type),
            model=SARVAM_STT_MODEL,
            language_code=lang_code
        )
        transcript = res.transcript.strip() if res and hasattr(res, "transcript") else ""
        log.info(f"[STT] Transcription result: '{transcript}'")
        return {
            "status": "SUCCESS",
            "transcript": transcript,
            "language_code": lang_code
        }
    except Exception as e:
        log.error(f"[STT] Sarvam transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice transcription failed: {str(e)}")

@router.post("/tts")
async def generate_speech(req: TTSRequest):
    """Synthesizes high-fidelity voiceover using Sarvam AI (primary) with Edge TTS fallback."""
    lang = (req.language or "en").lower()
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    cache_key = f"{lang}::{text}"
    if cache_key in _AUDIO_CACHE:
        log.info(f"[TTS] Serving cached audio for {lang} ({len(_AUDIO_CACHE[cache_key])} bytes)")
        return Response(content=_AUDIO_CACHE[cache_key], media_type="audio/wav")

    # 1. Primary: Try Sarvam AI Bulbul TTS
    sarvam_client = get_sarvam_client()
    if sarvam_client:
        try:
            sarvam_lang = SARVAM_LANG_CODES.get(lang, "hi-IN")
            log.info(f"[TTS] Synthesizing speech with Sarvam AI ({sarvam_lang}) for: '{text[:40]}...'")
            res = sarvam_client.text_to_speech.convert(
                text=text,
                language_code=sarvam_lang,
                speaker="aditya",
                model=SARVAM_TTS_MODEL
            )
            if res and res.audios:
                audio_data = base64.b64decode(res.audios[0])
                _AUDIO_CACHE[cache_key] = audio_data
                log.info(f"[TTS] Successfully generated {len(audio_data)} bytes via Sarvam AI ({sarvam_lang})")
                return Response(content=audio_data, media_type="audio/wav")
        except Exception as e:
            log.warning(f"[TTS] Sarvam TTS call failed ({e}). Falling back to Edge TTS.")

    # 2. Resilient Fallback: Edge TTS
    if edge_tts:
        voice = EDGE_TTS_VOICES.get(lang, "en-IN-NeerjaNeural")
        try:
            log.info(f"[TTS] Synthesizing speech with Edge TTS ({voice}) for: '{text[:40]}...'")
            communicate = edge_tts.Communicate(text, voice)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            audio_data = b"".join(chunks)
            if audio_data:
                _AUDIO_CACHE[cache_key] = audio_data
                log.info(f"[TTS] Successfully generated {len(audio_data)} bytes via Edge TTS ({voice})")
                return Response(content=audio_data, media_type="audio/mpeg")
        except Exception as e:
            log.error(f"[TTS] Edge TTS generation error: {e}")

    raise HTTPException(status_code=500, detail="Speech synthesis failed on all available engines.")

@router.post("/stego/generate")
def api_generate_stego(req: StegoGenerateRequest):
    """Generates the merchant standee with embedded invisible QR code."""
    try:
        return generate_stego_qr_template(req.merchant_id)
    except Exception as e:
        log.error(f"[STEGO] Generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stego/verify")
def api_verify_stego(req: StegoVerifyRequest):
    """Verifies counter QR authenticity by decoding hidden stego bitplanes from base64."""
    try:
        b64_str = req.image_base64
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(b64_str)
        return verify_stego_qr_image(img_bytes, req.merchant_id)
    except Exception as e:
        log.error(f"[STEGO] Verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stego/verify-upload")
async def api_verify_stego_upload(file: UploadFile = File(...), merchant_id: str = Form("M-101")):
    """Verifies counter QR authenticity by decoding hidden stego bitplanes from uploaded file."""
    try:
        img_bytes = await file.read()
        return verify_stego_qr_image(img_bytes, merchant_id)
    except Exception as e:
        log.error(f"[STEGO] Verify upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stego/sample-tampered")
def api_sample_tampered(merchant_id: str = "M-101"):
    """Returns sample tampered template with rogue thief sticker/marker dot for 1-click testing."""
    try:
        return create_sample_tampered_image(merchant_id)
    except Exception as e:
        log.error(f"[STEGO] Sample tampered error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/ask-agent")
async def api_ask_voice_agent(req: QRVoiceRequest):
    """Processes merchant voice inquiry regarding QR authenticity and speaks back directly via neural TTS."""
    voice_res = process_qr_voice_query(
        merchant_id=req.merchant_id,
        query=req.query,
        is_verified=req.is_verified,
        is_valid=req.is_valid,
        integrity_score=req.integrity_score,
        scanned_vpa=req.scanned_vpa,
        language=req.language or "en"
    )
    
    # Synthesize audio bytes in background
    audio_base64 = None
    spoken_text = voice_res["spoken_text"]
    lang = (req.language or "en").lower()
    
    # 1. Try Sarvam AI TTS
    sarvam_client = get_sarvam_client()
    if sarvam_client:
        try:
            sarvam_lang = SARVAM_LANG_CODES.get(lang, "hi-IN")
            res = sarvam_client.text_to_speech.convert(
                text=spoken_text,
                language_code=sarvam_lang,
                speaker="aditya",
                model=SARVAM_TTS_MODEL
            )
            if res and res.audios:
                audio_base64 = res.audios[0]
        except Exception as e:
            log.warning(f"[VOICE_AGENT] Sarvam TTS failed: {e}")
            
    # 2. Try Edge TTS fallback
    if not audio_base64 and edge_tts:
        voice = EDGE_TTS_VOICES.get(lang, "en-IN-NeerjaNeural")
        try:
            communicate = edge_tts.Communicate(spoken_text, voice)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            raw_audio = b"".join(chunks)
            if raw_audio:
                audio_base64 = base64.b64encode(raw_audio).decode("utf-8")
        except Exception as e:
            log.warning(f"[VOICE_AGENT] Edge TTS fallback failed: {e}")

    voice_res["audio_base64"] = audio_base64
    return voice_res


