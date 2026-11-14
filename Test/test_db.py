import sys
from pathlib import Path

# Add backend directory to sys.path (supports running from Test/ or project root)
test_dir = Path(__file__).parent.resolve()
project_root = test_dir.parent if test_dir.name.lower() == "test" else test_dir
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from database import init_db, run_query

def test_database_initialization():
    print(">>> [TEST 1] Initializing and Seeding Database...")
    init_db(seed=True)
    print("  [PASSED] init_db() executed without errors.")

def test_merchant_retrieval():
    print(">>> [TEST 2] Verifying Merchants...")
    merchants = run_query("SELECT id, name, username, bank_name FROM merchants")
    assert len(merchants) == 5, f"Expected 5 merchants, got {len(merchants)}"
    print(f"  [PASSED] 5 Merchants verified:")
    for m in merchants:
        print(f"    - {m['id']}: {m['name']} (@{m['username']}) | {m['bank_name']}")

def test_scenarios_data():
    print(">>> [TEST 3] Verifying 5 Scenario Data Integrity...")
    
    # Scenario 1 (Ramesh): Batch HELD with NPCI_CLEARING_TIMEOUT
    s1 = run_query("SELECT * FROM settlement_batches WHERE merchant_id = 'M-101' AND status = 'HELD'")
    assert len(s1) == 1, "Scenario 1 batch not found"
    assert s1[0]['hold_reason'] == 'NPCI_CLEARING_TIMEOUT'
    print(f"  [PASSED] Scenario 1 (Ramesh): Batch {s1[0]['batch_code']} stuck on NPCI timeout (Amount: ₹{s1[0]['total_amount']})")

    # Scenario 2 (Sharmaji): Batch HELD with HIGH_VALUE_VELOCITY_LIMIT (>25k)
    s2 = run_query("SELECT * FROM settlement_batches WHERE merchant_id = 'M-102' AND status = 'HELD'")
    assert len(s2) == 1, "Scenario 2 batch not found"
    assert s2[0]['total_amount'] == 78000.0
    assert s2[0]['hold_reason'] == 'HIGH_VALUE_VELOCITY_LIMIT'
    print(f"  [PASSED] Scenario 2 (Sharmaji): High value ₹{s2[0]['total_amount']} held for human approval")

    # Scenario 3 (Chai Point): Soundbox DROPPED chime & TEMPORARY_DISCONNECT
    s3_sb = run_query("SELECT * FROM soundbox_devices WHERE merchant_id = 'M-103'")
    assert len(s3_sb) == 1
    assert s3_sb[0]['last_chime_status'] == 'DROPPED'
    print(f"  [PASSED] Scenario 3 (Chai Point): Soundbox {s3_sb[0]['device_id']} dropped chime verified")

    # Scenario 4 (Verma Meds): Duplicate reversal
    s4 = run_query("SELECT * FROM transactions WHERE merchant_id = 'M-104'")
    assert len(s4) == 2
    reversed_tx = [t for t in s4 if t['status'] == 'REVERSED']
    assert len(reversed_tx) == 1
    print(f"  [PASSED] Scenario 4 (Verma Meds): Duplicate transaction {reversed_tx[0]['order_id']} in auto-reversal verified")

    # Scenario 5 (Gupta Sweets): HDFC rail degradation
    s5 = run_query("SELECT * FROM transactions WHERE merchant_id = 'M-105' AND status = 'FAILED'")
    assert len(s5) >= 2
    print(f"  [PASSED] Scenario 5 (Gupta Sweets): {len(s5)} failed transactions due to gateway latency verified")

if __name__ == "__main__":
    try:
        test_database_initialization()
        test_merchant_retrieval()
        test_scenarios_data()
        print("\n=======================================================")
        print("ALL DATABASE TESTS PASSED! (PHASE 1 VERIFICATION 100% OK)")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAILED] Test failed with error: {e}")
        sys.exit(1)

