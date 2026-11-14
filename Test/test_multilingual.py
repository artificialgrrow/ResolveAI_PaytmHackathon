import os
import sys

# Ensure backend modules are on path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parent_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db
from agent_engine import process_incident_stream, approve_incident_stream, MULTILINGUAL_TEMPLATES

def test_all_10_languages():
    print("\n--- Verifying Multilingual Templates Coverage ---")
    languages = ['en', 'hi', 'mr', 'gu', 'bn', 'ta', 'te', 'kn', 'ml', 'pa']
    for scenario in ['S1_RESOLVED', 'S2_APPROVED', 'S3_RESOLVED', 'S4_RESOLVED', 'S5_RESOLVED', 'SAFETY_HOLD', 'DEFAULT_RESOLVED']:
        assert scenario in MULTILINGUAL_TEMPLATES, f"Missing scenario: {scenario}"
        for lang in languages:
            assert lang in MULTILINGUAL_TEMPLATES[scenario], f"Missing lang {lang} in {scenario}"
            template_text = MULTILINGUAL_TEMPLATES[scenario][lang]
            assert len(template_text) > 10, f"Template for {scenario}[{lang}] too short"
    print("  [PASSED] All 7 scenarios have verified templates across all 10 Indian languages.")

def test_marathi_incident_stream():
    print("\n--- Testing Marathi (mr) Incident Stream Execution ---")
    init_db(force_seed=True)
    # Ramesh Kirana prompt in Marathi
    marathi_query = "माझ्या सकाळच्या विक्रीचे ₹4,500 अजूनही माझ्या बँक खात्यात जमा झाले नाहीत. कृपया तपासा."
    events = list(process_incident_stream("M-101", marathi_query, language="mr"))
    
    assert len(events) >= 4, f"Expected at least 4 events, got {len(events)}"
    
    # Internal operations in English
    manager_event = events[0]
    assert "Manager Agent" in manager_event["agent"]
    assert "safety" in manager_event["message"].lower() or "merchant" in manager_event["message"].lower()
    
    investigator_event = next(e for e in events if e["agent"] == "Investigator Agent" and e["status"] == "TOOL_CALL")
    assert "SQL" in investigator_event["message"]
    
    # Final Verification event MUST be in Marathi
    resolved_event = next(e for e in events if e["agent"] == "Verification Agent" and e["status"] == "RESOLVED")
    assert "बँक UTR" in resolved_event["message"] or "खात्यात" in resolved_event["message"]
    print(f"  [PASSED] Marathi final response: {resolved_event['message']}")

def test_hindi_approval_stream():
    print("\n--- Testing Hindi (hi) Supervisor Approval Stream ---")
    init_db(force_seed=True)
    hindi_query = "ग्राहक ने QR से ₹78,000 का स्मार्ट टीवी खरीदा, लेकिन सेटलमेंट होल्ड पर दिख रहा है।"
    events = list(process_incident_stream("M-102", hindi_query, language="hi"))
    
    hold_event = next(e for e in events if e["status"] == "AWAITING_APPROVAL")
    incident_id = hold_event["details"]["incident_id"]
    
    # Check that localized warning is in Hindi
    assert "सुरक्षा सीमा" in hold_event["details"]["merchant_warning"] or "पर्यवेक्षक" in hold_event["details"]["merchant_warning"]
    
    # Resume with approval in Hindi
    approval_events = list(approve_incident_stream(incident_id, True, "Approved KYC", language="hi"))
    resolved_event = next(e for e in approval_events if e["status"] == "RESOLVED")
    assert "पर्यवेक्षक" in resolved_event["message"] or "बैंक UTR" in resolved_event["message"]
    print(f"  [PASSED] Hindi approved response: {resolved_event['message']}")

def test_gujarati_soundbox_chime():
    print("\n--- Testing Gujarati (gu) Soundbox Incident Stream ---")
    init_db(force_seed=True)
    gu_query = "ગ્રાહકે ચા માટે ₹60 આપ્યા, પણ સાઉન્ડબોક્સે કંઈ બોલ્યું નહીં!"
    events = list(process_incident_stream("M-103", gu_query, language="gu"))
    
    resolved_event = next(e for e in events if e["agent"] == "Verification Agent" and e["status"] == "RESOLVED")
    assert "સાઉન્ડબોક્સ" in resolved_event["message"] or "પેટીએમ" in resolved_event["message"]
    print(f"  [PASSED] Gujarati resolved response: {resolved_event['message']}")

if __name__ == "__main__":
    test_all_10_languages()
    test_marathi_incident_stream()
    test_hindi_approval_stream()
    test_gujarati_soundbox_chime()
    print("\n>>> ALL MULTILINGUAL VERIFICATIONS PASSED 100%! <<<\n")

