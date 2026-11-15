import os
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Database File Path & Environment
DB_DIR = Path(__file__).parent.resolve()
DB_PATH = DB_DIR / "paytm_resolve.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

def get_connection():
    """Returns a connection to SQLite (default zero-config) or PostgreSQL if DATABASE_URL is set."""
    if DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"):
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            print(f"[DB] PostgreSQL connection error ({e}). Falling back to local SQLite.")

    # Default: Zero-config SQLite with dictionary row factory
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(seed: Optional[bool] = None, force_seed: bool = False):
    """
    Initializes tables, creates performance indices, and automatically seeds demo data
    if the database is empty. Accepts both `seed=True` and `force_seed=True`.
    This guarantees that anyone running 'python main.py' has a complete, working setup
    out of the box with zero manual steps.
    """
    should_force = force_seed or (seed is True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Merchants Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        business_type TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        ifsc TEXT NOT NULL,
        phone TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        merchant_id TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL, -- SUCCESS, PENDING, FAILED, REVERSED
        payment_mode TEXT NOT NULL, -- UPI_QR, SOUNDBOX_QR, CARD, NETBANKING
        customer_vpa TEXT NOT NULL,
        rrn TEXT NOT NULL,
        failure_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    );
    """)

    # 3. Settlement Batches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settlement_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_code TEXT UNIQUE NOT NULL,
        merchant_id TEXT NOT NULL,
        order_id TEXT,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL, -- HELD, PROCESSING, SETTLED, FAILED
        rail TEXT NOT NULL, -- NPCI_PRIMARY, IMPS_SECONDARY, NEFT, RTGS
        hold_reason TEXT,
        utr_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cleared_at TIMESTAMP,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    );
    """)

    # 4. Soundbox Devices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS soundbox_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT UNIQUE NOT NULL,
        merchant_id TEXT NOT NULL,
        sim_status TEXT NOT NULL, -- ONLINE, TEMPORARY_DISCONNECT, OFFLINE
        battery_level INTEGER NOT NULL,
        last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_chime_status TEXT NOT NULL, -- SUCCESS, DROPPED, PENDING
        firmware_version TEXT NOT NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    );
    """)

    # 5. Incident Resolution Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incident_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT UNIQUE NOT NULL,
        merchant_id TEXT NOT NULL,
        query TEXT NOT NULL,
        status TEXT NOT NULL, -- INVESTIGATING, AWAITING_APPROVAL, RESOLVED, ESCALATED
        resolution_notes TEXT,
        utr_number TEXT,
        action_taken TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    );
    """)

    # Performance Indices (Optimized Lookups & No Full Table Scans)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions (merchant_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_order ON transactions (order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_merchant ON settlement_batches (merchant_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_code ON settlement_batches (batch_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_soundbox_merchant ON soundbox_devices (merchant_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_incident_merchant ON incident_logs (merchant_id);")

    # Check if database has merchants seeded
    cursor.execute("SELECT COUNT(*) FROM merchants")
    merchant_count = cursor.fetchone()[0]

    # Auto-seed if database is empty, or if explicitly requested
    if merchant_count == 0 or should_force:
        _seed_data(conn)
        print("[DATABASE] Auto-seeded 5 demo merchant scenarios into empty database.")
    else:
        print(f"[DATABASE] Database verified with {merchant_count} merchants.")

    conn.commit()
    conn.close()

def _seed_data(conn):
    """Seeds rich, realistic data for 5 merchant personas."""
    cursor = conn.cursor()

    # Clear existing demo data to ensure pristine reproducible states
    cursor.execute("DELETE FROM incident_logs")
    cursor.execute("DELETE FROM soundbox_devices")
    cursor.execute("DELETE FROM settlement_batches")
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM merchants")

    now = datetime.datetime.now()
    two_hours_ago = (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    one_hour_ago = (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    fifteen_min_ago = (now - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

    # Seed 5 Merchants
    merchants = [
        ("M-101", "Ramesh Kirana Store", "ramesh_kirana", "paytm123", "Retail Grocery", "HDFC Bank", "XXXXXX4918", "HDFC0001234", "+91 98765 43210"),
        ("M-102", "Sharmaji Electronics", "sharma_electro", "paytm123", "Consumer Electronics", "State Bank of India", "XXXXXX9082", "SBIN0004567", "+91 98220 12345"),
        ("M-103", "Chai Point Stall", "chai_point", "paytm123", "Food & Beverage", "ICICI Bank", "XXXXXX3119", "ICIC0002468", "+91 97110 56789"),
        ("M-104", "Verma Medical Hall", "verma_meds", "paytm123", "Healthcare / Pharmacy", "Axis Bank", "XXXXXX6643", "UTIB0000890", "+91 99345 67890"),
        ("M-105", "Gupta Sweets & Snacks", "gupta_sweets", "paytm123", "Confectionery / Restaurant", "Punjab National Bank", "XXXXXX7721", "PUNB0001122", "+91 98100 23456")
    ]
    cursor.executemany("""
    INSERT INTO merchants (id, name, username, password, business_type, bank_name, account_number, ifsc, phone)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, merchants)

    # 1. Scenario 1 (Ramesh Kirana): ₹4,500 morning sales, batch #B-402 held due to NPCI sync timeout
    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-89104', 'M-101', 4500.0, 'SUCCESS', 'UPI_QR', 'rohit.kumar@okhdfcbank', '408912389104', NULL, ?)
    """, (two_hours_ago,))

    cursor.execute("""
    INSERT INTO settlement_batches (batch_code, merchant_id, order_id, total_amount, status, rail, hold_reason, utr_number, created_at, cleared_at)
    VALUES ('B-402', 'M-101', 'PTM-89104', 4500.0, 'HELD', 'NPCI_PRIMARY', 'NPCI_CLEARING_TIMEOUT', NULL, ?, NULL)
    """, (two_hours_ago,))

    cursor.execute("""
    INSERT INTO soundbox_devices (device_id, merchant_id, sim_status, battery_level, last_heartbeat, last_chime_status, firmware_version)
    VALUES ('SB-8821', 'M-101', 'ONLINE', 92, ?, 'SUCCESS', 'v4.2.1-paytm')
    """, (fifteen_min_ago,))

    # 2. Scenario 2 (Sharmaji Electronics): ₹78,000 smart TV sale, held under velocity limit (>₹25k Human-in-Loop)
    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-77301', 'M-102', 78000.0, 'SUCCESS', 'UPI_QR', 'ananya.sharma@okaxis', '409923847301', NULL, ?)
    """, (one_hour_ago,))

    cursor.execute("""
    INSERT INTO settlement_batches (batch_code, merchant_id, order_id, total_amount, status, rail, hold_reason, utr_number, created_at, cleared_at)
    VALUES ('B-709', 'M-102', 'PTM-77301', 78000.0, 'HELD', 'RTGS_PRIMARY', 'HIGH_VALUE_VELOCITY_LIMIT', NULL, ?, NULL)
    """, (one_hour_ago,))

    cursor.execute("""
    INSERT INTO soundbox_devices (device_id, merchant_id, sim_status, battery_level, last_heartbeat, last_chime_status, firmware_version)
    VALUES ('SB-9014', 'M-102', 'ONLINE', 84, ?, 'SUCCESS', 'v4.2.1-paytm')
    """, (fifteen_min_ago,))

    # 3. Scenario 3 (Chai Point Stall): Customer claims payment with fake screenshot; Soundbox stayed silent
    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-33100', 'M-103', 20.0, 'SUCCESS', 'SOUNDBOX_QR', 'manish.verma@paytm', '409934783100', NULL, ?)
    """, (two_hours_ago,))

    cursor.execute("""
    INSERT INTO settlement_batches (batch_code, merchant_id, order_id, total_amount, status, rail, hold_reason, utr_number, created_at, cleared_at)
    VALUES ('B-115', 'M-103', 'PTM-33100', 20.0, 'SETTLED', 'IMPS_SECONDARY', NULL, 'UTR-8012399120', ?, ?)
    """, (two_hours_ago, one_hour_ago))

    cursor.execute("""
    INSERT INTO soundbox_devices (device_id, merchant_id, sim_status, battery_level, last_heartbeat, last_chime_status, firmware_version)
    VALUES ('SB-4402', 'M-103', 'ONLINE', 88, ?, 'IDLE_WAITING', 'v4.2.1-paytm')
    """, (fifteen_min_ago,))

    # 4. Scenario 4 (Verma Medical): ₹1,200 duplicate debit; 1 success + 1 in NPCI auto-reversal queue
    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-55101', 'M-104', 1200.0, 'SUCCESS', 'UPI_QR', 'vikram.patel@okicici', '408991205101', NULL, ?)
    """, (two_hours_ago,))

    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-55102', 'M-104', 1200.0, 'REVERSED', 'UPI_QR', 'vikram.patel@okicici', '408991205102', 'DUPLICATE_UPI_DEBIT_AUTO_REVERSAL_INITIATED', ?)
    """, (two_hours_ago,))

    cursor.execute("""
    INSERT INTO settlement_batches (batch_code, merchant_id, order_id, total_amount, status, rail, hold_reason, utr_number, created_at, cleared_at)
    VALUES ('B-334', 'M-104', 'PTM-55101', 1200.0, 'SETTLED', 'IMPS_SECONDARY', NULL, 'UTR-7788992211', ?, ?)
    """, (two_hours_ago, one_hour_ago))

    cursor.execute("""
    INSERT INTO soundbox_devices (device_id, merchant_id, sim_status, battery_level, last_heartbeat, last_chime_status, firmware_version)
    VALUES ('SB-6670', 'M-104', 'ONLINE', 95, ?, 'SUCCESS', 'v4.2.1-paytm')
    """, (fifteen_min_ago,))

    # 5. Scenario 5 (Gupta Sweets): HDFC acquiring bank rail degradation; route switch to ICICI backup rail
    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-99121', 'M-105', 850.0, 'FAILED', 'UPI_QR', 'rahul.gupta@okhdfcbank', '409988119121', 'ACQUIRING_BANK_HDFC_DEGRADATION_503', ?)
    """, (fifteen_min_ago,))

    cursor.execute("""
    INSERT INTO transactions (order_id, merchant_id, amount, status, payment_mode, customer_vpa, rrn, failure_reason, created_at)
    VALUES ('PTM-99122', 'M-105', 420.0, 'FAILED', 'UPI_QR', 'deepak.mehta@okhdfcbank', '409988119122', 'ACQUIRING_BANK_HDFC_DEGRADATION_503', ?)
    """, (fifteen_min_ago,))

    cursor.execute("""
    INSERT INTO settlement_batches (batch_code, merchant_id, order_id, total_amount, status, rail, hold_reason, utr_number, created_at, cleared_at)
    VALUES ('B-890', 'M-105', 'PTM-99121', 1270.0, 'PROCESSING', 'HDFC_PRIMARY_GATEWAY', 'BANK_GATEWAY_LATENCY_SPIKE', NULL, ?, NULL)
    """, (fifteen_min_ago,))

    cursor.execute("""
    INSERT INTO soundbox_devices (device_id, merchant_id, sim_status, battery_level, last_heartbeat, last_chime_status, firmware_version)
    VALUES ('SB-1092', 'M-105', 'ONLINE', 79, ?, 'SUCCESS', 'v4.2.1-paytm')
    """, (fifteen_min_ago,))

    conn.commit()

def run_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Safe execution of read/write queries, returning list of dictionaries."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    
    # Check if query returned rows
    if cursor.description:
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        results = [{"rows_affected": cursor.rowcount}]
        conn.commit()
        
    conn.close()
    return results

if __name__ == "__main__":
    print("[INIT] Initializing and seeding Paytm ResolveAI SQLite Database...")
    init_db(seed=True)
    print("[SUCCESS] Database successfully initialized at:", DB_PATH)
    
    # Quick sanity test
    merchants = run_query("SELECT id, name, username, bank_name FROM merchants")
    print(f"[VERIFY] Loaded {len(merchants)} merchants:")
    for m in merchants:
        print(f"  - {m['id']}: {m['name']} (@{m['username']}) -> {m['bank_name']}")

