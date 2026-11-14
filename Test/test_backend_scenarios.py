import sys
from pathlib import Path

# Add backend directory to sys.path (supports running from Test/ or project root)
test_dir = Path(__file__).parent.resolve()
project_root = test_dir.parent if test_dir.name.lower() == "test" else test_dir
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from database import init_db, run_query
from agent_engine import process_incident_stream, approve_incident_stream

def run_scenario_test(scenario_num: int, title: str, merchant_id: str, message: str):
    print(f"\n=======================================================")
    print(f">>> [SCENARIO {scenario_num}] {title}")
    print(f"Merchant ID: {merchant_id} | Query: '{message}'")
    print(f"=======================================================")
    
    events = list(process_incident_stream(merchant_id=merchant_id, message=message))
    for ev in events:
        step_num = ev["step"]
        agent = ev["agent"]
        status = ev["status"]
        msg = ev["message"]
        print(f"  [Step {step_num}] [{agent}] [{status}] {msg[:90]}...")
    
    last_event = events[-1]
    return events, last_event

def test_all_scenarios():
    print(">>> Initializing clean database for scenario testing...")
    init_db(seed=True)

    # 1. Scenario 1: Ramesh Kirana (Auto-Resolution <= 25k)
    s1_events, s1_last = run_scenario_test(
        1, "Ramesh Kirana: ₹4,500 Stuck Morning Sales",
        "M-101", "My 4500 morning QR payment hasn't reached my bank account yet."
    )
    assert s1_last["status"] == "RESOLVED", f"Expected RESOLVED, got {s1_last['status']}"
    assert "UTR" in s1_last["message"], "UTR missing from resolution message"
    print("  --> SCENARIO 1 PASSED: Resolved with verified bank UTR.")

    # 2. Scenario 2: Sharmaji Electronics (Threshold Breach > 25k -> Human Approval)
    s2_events, s2_last = run_scenario_test(
        2, "Sharmaji Electronics: ₹78,000 High-Value Settlement Held",
        "M-102", "Customer paid 78000 for Smart TV, settlement is on hold."
    )
    assert s2_last["status"] == "AWAITING_APPROVAL", f"Expected AWAITING_APPROVAL, got {s2_last['status']}"
    incident_id = s2_last["details"]["incident_id"]
    print(f"  --> SCENARIO 2 (PART 1) PASSED: Correctly paused for supervisor approval (Incident ID: {incident_id}).")

    # Resume Scenario 2 via Human Approval
    print("  --> Simulating Supervisor Approval...")
    approval_events = list(approve_incident_stream(incident_id=incident_id, approved=True, notes="Verified customer invoice"))
    for ev in approval_events:
        print(f"    [Step {ev['step']}] [{ev['agent']}] [{ev['status']}] {ev['message'][:90]}...")
    
    assert approval_events[-1]["status"] == "RESOLVED"
    print("  --> SCENARIO 2 (PART 2) PASSED: Approved override cleared high-value settlement.")

    # 3. Scenario 3: Chai Point (Soundbox Speech Issue)
    s3_events, s3_last = run_scenario_test(
        3, "Chai Point Stall: Soundbox Did Not Speak",
        "M-103", "Customer paid 60 rupees for tea, but Soundbox did not announce."
    )
    assert s3_last["status"] == "RESOLVED", f"Expected RESOLVED, got {s3_last['status']}"
    assert "Paytm par 60" in s3_last["message"] or "Soundbox" in s3_last["message"]
    print("  --> SCENARIO 3 PASSED: Verified payment and triggered OTA Soundbox chime.")

    # 4. Scenario 4: Verma Meds (Duplicate Debit & Auto-Reversal)
    s4_events, s4_last = run_scenario_test(
        4, "Verma Medical: Customer Claimed Charged Twice",
        "M-104", "Customer says they got debited twice for medicine."
    )
    assert s4_last["status"] == "RESOLVED", f"Expected RESOLVED, got {s4_last['status']}"
    assert "duplicate" in s4_last["message"].lower() or "reversed" in s4_last["message"].lower()
    print("  --> SCENARIO 4 PASSED: Reassured merchant with verified reversal reference.")

    # 5. Scenario 5: Gupta Sweets (Bank Rail Outage / Route Switch)
    s5_events, s5_last = run_scenario_test(
        5, "Gupta Sweets: Multiple Recent Payment Declines",
        "M-105", "Why are all QR payments failing since afternoon?"
    )
    assert s5_last["status"] == "RESOLVED", f"Expected RESOLVED, got {s5_last['status']}"
    assert "ICICI" in s5_last["message"] or "re-routed" in s5_last["message"].lower()
    print("  --> SCENARIO 5 PASSED: Automatically re-routed traffic to backup acquiring gateway.")

if __name__ == "__main__":
    try:
        test_all_scenarios()
        print("\n=======================================================")
        print("ALL 5 SCENARIOS VERIFIED SUCCESSFULLY! (PHASE 2 OK)")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAILED] Backend scenario test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

