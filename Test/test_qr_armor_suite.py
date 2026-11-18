import sys
from pathlib import Path
import base64

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import init_db, run_query
from stego_service import generate_stego_qr_template, create_sample_tampered_image, verify_stego_qr_image
from agent_engine import process_qr_voice_query

def run_suite():
    print("=" * 70)
    print("PAYTM QR ARMOR • MASTER VERIFICATION TEST SUITE")
    print("=" * 70)

    # Step 1: Database Initialization
    print("\n[TEST 1] Initializing and verifying database...")
    init_db(force_seed=True)
    merchants = run_query("SELECT id, name, username FROM merchants")
    assert len(merchants) >= 5, "Database must have 5 demo merchants"
    print(f"✓ Database verified with {len(merchants)} merchants.")

    # Step 2: Standee & Cryptographic Provenance Generation
    print("\n[TEST 2] Generating Steganographic Standee for M-101 (Ramesh Kirana)...")
    stego_res = generate_stego_qr_template("M-101")
    assert stego_res["status"] == "SUCCESS"
    assert "stego_image_base64" in stego_res
    assert "extracted_qr_base64" in stego_res
    assert stego_res["vpa"] == "ramesh_kirana@paytm"
    assert "HMAC-SHA256" in stego_res["issued_payload"]["digital_signature"]
    print(f"✓ Generated standee with HMAC signature: {stego_res['issued_payload']['digital_signature'][:28]}...")
    print(f"✓ Destination VPA: {stego_res['issued_payload']['destination_vpa']}")

    # Step 3: Verify Genuine Standee
    print("\n[TEST 3] Verifying Genuine Standee...")
    genuine_bytes = base64.b64decode(stego_res["stego_image_base64"])
    v_genuine = verify_stego_qr_image(genuine_bytes, "M-101")
    assert v_genuine["is_valid"] is True, "Genuine image must be valid"
    assert v_genuine["status"] == "AUTHENTIC_VERIFIED"
    assert v_genuine["integrity_score"] >= 85.0
    assert v_genuine["scanned_payload"]["destination_vpa"] == "ramesh_kirana@paytm"
    print(f"✓ Genuine verification passed: Status={v_genuine['status']}, Integrity={v_genuine['integrity_score']}%")

    # Step 4: Simulate Physical Sticker Tampering (Delhi Police Fraud Scenario)
    print("\n[TEST 4] Simulating Physical Sticker Tampering (Rogue QR pasted over standee)...")
    tampered_res = create_sample_tampered_image("M-101")
    assert tampered_res["status"] == "SUCCESS"
    assert tampered_res["rogue_payload"]["destination_vpa"] == "thief_scam99@ybl"
    print(f"✓ Created physically altered standee with rogue destination: {tampered_res['rogue_payload']['destination_vpa']}")

    # Step 5: Verify Tampered Standee (Dual-Binding Failure)
    print("\n[TEST 5] Auditing Tampered Standee with Dual-Binding Engine...")
    tampered_bytes = base64.b64decode(tampered_res["tampered_image_base64"])
    v_tampered = verify_stego_qr_image(tampered_bytes, "M-101")
    assert v_tampered["is_valid"] is False, "Tampered image must be flagged"
    assert v_tampered["status"] == "TAMPERED_FRAUD_DETECTED"
    assert v_tampered["scanned_payload"]["destination_vpa"] == "thief_scam99@ybl"
    assert v_tampered["integrity_score"] < 85.0
    print(f"✓ Tampering correctly caught! Status={v_tampered['status']}, Scanned VPA={v_tampered['scanned_payload']['destination_vpa']}, Integrity={v_tampered['integrity_score']}%")

    # Step 6: Verify Autonomous Remediation in DB
    print("\n[TEST 6] Verifying Autonomous Security Remediation in Database...")
    frozen_batches = run_query("SELECT batch_code, status, hold_reason FROM settlement_batches WHERE merchant_id = 'M-101' AND status = 'HELD'")
    assert len(frozen_batches) > 0, "Settlement batches must be frozen"
    assert frozen_batches[0]["hold_reason"] == "PHYSICAL_QR_TAMPER_DETECTED"
    print(f"✓ Payout rail frozen: Batch {frozen_batches[0]['batch_code']} marked {frozen_batches[0]['status']} ({frozen_batches[0]['hold_reason']})")

    sb = run_query("SELECT device_id, last_chime_status FROM soundbox_devices WHERE merchant_id = 'M-101' LIMIT 1")[0]
    assert sb["last_chime_status"] == "FRAUD_ALERT_EMITTED"
    print(f"✓ Soundbox {sb['device_id']} alert emitted: {sb['last_chime_status']}")

    logs = run_query("SELECT incident_id, action_taken FROM incident_logs WHERE merchant_id = 'M-101' ORDER BY id DESC LIMIT 1")[0]
    assert "AUTONOMOUS_PAYOUT_FREEZE" in logs["action_taken"]
    print(f"✓ Incident docket logged: {logs['incident_id']} ({logs['action_taken']})")

    # Step 7: Voice Agent Multilingual Response Testing
    print("\n[TEST 7] Testing Autonomous Voice Agent Responses across Indian Languages...")
    languages_to_test = ["en", "hi", "mr", "gu", "ta"]
    for lang in languages_to_test:
        voice_res = process_qr_voice_query(
            merchant_id="M-101",
            query="Is this QR valid?",
            is_verified=True,
            is_valid=False,
            integrity_score=24.8,
            scanned_vpa="thief_scam99@ybl",
            language=lang
        )
        assert voice_res["status"] == "TAMPERED"
        assert len(voice_res["spoken_text"]) > 20
        print(f"  [{lang.upper()}] Spoken Alert: {voice_res['spoken_text'][:65]}...")

    print("\n" + "=" * 70)
    print("ALL 7 MASTER VERIFICATION TESTS PASSED SUCCESSFULLY! (100% HEALTHY)")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
