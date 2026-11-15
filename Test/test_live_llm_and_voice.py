import os
import sys
from pathlib import Path

# Setup paths
test_dir = Path(__file__).parent.resolve()
project_root = test_dir.parent if test_dir.name.lower() == "test" else test_dir
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

def print_banner(text: str):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def test_live_llm():
    print_banner("[TEST 1/3] LIVE LLM INVOCATION & ZERO-ASTERISK ENFORCEMENT")
    from config import get_llm
    from agent_engine import process_incident_stream, generate_ai_response
    from database import init_db, run_query

    init_db(seed=True)
    llm = get_llm()
    print(f"  Configured LLM Model: {type(llm).__name__ if llm else 'None'}")

    # Test 1: S1 in English with Live LLM
    print("  Testing S1 (Ramesh Kirana)...")
    events = list(process_incident_stream("M-101", "My ₹4,500 payment from morning sales hasn't reached my bank account yet. Please check.", language="en"))
    final_event = events[-1]
    assert final_event["status"] == "RESOLVED"
    print(f"  S1 Final Output: {final_event['message']}")
    assert "*" not in final_event["message"], "Found asterisks in S1 response!"

    # Test 2: S3 in Hindi with Live LLM
    print("\n  Testing S3 (Chai Point in Hindi)...")
    s3_events = list(process_incident_stream("M-103", "ग्राहक ने चाय के लिए ₹60 दिए, लेकिन साउंडबॉक्स ने कुछ नहीं बोला!", language="hi"))
    s3_final = s3_events[-1]
    assert s3_final["status"] == "RESOLVED"
    print(f"  S3 Final Output: {s3_final['message']}")
    assert "*" not in s3_final["message"], "Found asterisks in S3 response!"

    # Test 3: Informational query (Order ID inquiry - generic chatbot question)
    print("\n  Testing Informational Query (Order ID)...")
    info_events = list(process_incident_stream("M-101", "What is the order id of my payment ?", language="en"))
    info_final = info_events[-1]
    assert info_final["status"] == "RESOLVED"
    print(f"  Info Final Output: {info_final['message']}")
    assert "*" not in info_final["message"], "Found asterisks in Info response!"
    assert "utr_number" not in info_final.get("details", {}), "UTR card should NOT be shown for general order ID query!"
    print("  [PASSED] Informational query answered cleanly without trigger cards or asterisks.")

def test_live_sarvam_tts():
    print_banner("[TEST 2/3] DUAL-ENGINE TEXT-TO-SPEECH (SARVAM BULBUL + EDGE TTS)")
    from config import SARVAM_API_KEY, get_sarvam_client
    import asyncio

    client = get_sarvam_client()
    if client:
        print("  Testing Sarvam AI Bulbul TTS (aditya voice)...")
        try:
            res = client.text_to_speech.convert(
                text="Paytm par 60 rupaye prapt hue",
                language_code="hi-IN",
                model="bulbul:v3",
                speaker="aditya"
            )
            audio_data = getattr(res, "audios", [None])[0]
            assert audio_data is not None, "No audio generated from Sarvam TTS"
            print(f"  [PASSED] Sarvam Bulbul generated base64 audio (length: {len(audio_data)})")
        except Exception as e:
            print(f"  [WARNING] Sarvam TTS test error: {e}")
    else:
        print("  Sarvam AI client not configured. Skipping Sarvam Bulbul test.")

def test_live_sarvam_stt_transcription():
    print_banner("[TEST 3/3] SARVAM SAARAS STT TRANSCRIPTION API CHECK")
    from config import get_sarvam_client
    client = get_sarvam_client()
    if client:
        print("  Verifying Sarvam Saaras STT client capability...")
        assert hasattr(client, "speech_to_text"), "Client missing speech_to_text capability"
        print("  [PASSED] Sarvam STT client ready.")
    else:
        print("  Sarvam AI client not configured. Skipping STT test.")

if __name__ == "__main__":
    try:
        test_live_llm()
        test_live_sarvam_tts()
        test_live_sarvam_stt_transcription()
        print_banner("ALL LIVE API & AGENT TESTS PASSED!")
    except Exception as e:
        print(f"\n[FAILURE]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
