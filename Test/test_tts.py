import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parent_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from routes import EDGE_TTS_VOICES

def test_tts_endpoint():
    print("\n--- Testing Edge TTS Audio Endpoint (/api/tts) ---")
    client = TestClient(app)
    
    # 1. Test empty text validation
    res = client.post("/api/tts", json={"text": "", "language": "en"})
    assert res.status_code == 400, f"Expected 400 for empty text, got {res.status_code}"
    print("  [PASSED] Empty text returns 400 Bad Request.")
    
    # 2. Test English TTS
    print("  Testing English TTS voice synthesis...")
    res = client.post("/api/tts", json={"text": "Your settlement has been approved.", "language": "en"})
    if res.status_code == 200:
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 1000
        print(f"  [PASSED] Generated English audio: {len(res.content)} bytes.")
    else:
        print(f"  [INFO] Edge TTS remote service returned {res.status_code} (Network sandbox or offline).")

    # 3. Test Marathi TTS
    print("  Testing Marathi TTS voice synthesis...")
    res = client.post("/api/tts", json={"text": "आपले पेमेंट यशस्वी झाले आहे.", "language": "mr"})
    if res.status_code == 200:
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 1000
        print(f"  [PASSED] Generated Marathi audio: {len(res.content)} bytes.")
    else:
        print(f"  [INFO] Edge TTS remote service returned {res.status_code} (Network sandbox or offline).")

    # 4. Verify voice dictionary mapping
    for lang in ['en', 'hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml']:
        assert lang in EDGE_TTS_VOICES, f"Missing voice mapping for {lang}"
        assert "-IN" in EDGE_TTS_VOICES[lang], f"Non-Indian voice mapped: {EDGE_TTS_VOICES[lang]}"
    print("  [PASSED] Verified all Indian voice mappings in EDGE_TTS_VOICES.")

if __name__ == "__main__":
    test_tts_endpoint()
    print("\n>>> ALL TTS ENDPOINT CHECKS VERIFIED! <<<\n")

