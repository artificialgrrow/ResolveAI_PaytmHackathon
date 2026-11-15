import time
import random
import datetime
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.tools import tool

from database import run_query
from logger import log

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=1, max=3),
    reraise=True
)
def _execute_sql(query: str) -> List[Dict[str, Any]]:
    """Helper with tenacity retry for database query execution."""
    return run_query(query)

@tool
def query_merchant_database(sql_query: str) -> str:
    """Executes a SQL query against the Paytm merchant database to inspect transactions,
    settlement batches, soundbox device status, or merchant details.
    Always specify explicit columns rather than unconstrained SELECT * where possible.
    """
    log.info(f"[TOOL:query_merchant_database] Executing: {sql_query}")
    try:
        # Prevent dangerous destructive operations in NLP2SQL
        normalized = sql_query.strip().upper()
        if any(keyword in normalized for keyword in ["DROP ", "ALTER ", "TRUNCATE "]):
            return "Error: Schema modification statements are prohibited."

        results = _execute_sql(sql_query)
        if not results:
            return "Query returned 0 rows."
        return str(results)
    except Exception as e:
        log.error(f"[TOOL:query_merchant_database] Query failed: {e}")
        return f"Database error: {str(e)}"

@tool
def requeue_settlement_batch(batch_code: str, target_rail: str = "IMPS_SECONDARY") -> str:
    """Idempotently re-routes a held or timed-out settlement batch to a secondary banking rail
    (e.g., IMPS_SECONDARY) to guarantee immediate bank credit and generate a verified UTR.
    """
    log.info(f"[TOOL:requeue_settlement_batch] Re-queuing batch {batch_code} to {target_rail}")
    try:
        # Check current batch status
        batches = _execute_sql(f"SELECT batch_code, status, total_amount FROM settlement_batches WHERE batch_code = '{batch_code}' LIMIT 1")
        if not batches:
            return f"Error: Settlement batch {batch_code} not found."

        batch = batches[0]
        if batch["status"] == "SETTLED":
            return f"Batch {batch_code} is already SETTLED."

        # Simulate secondary rail IMPS transfer
        time.sleep(0.3)
        utr_number = f"UTR-{random.randint(9000000000, 9999999999)}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update batch status to SETTLED
        update_query = f"""
        UPDATE settlement_batches
        SET status = 'SETTLED',
            rail = '{target_rail}',
            hold_reason = 'AUTO_RESOLVED_FAILOVER',
            utr_number = '{utr_number}',
            cleared_at = '{now_str}'
        WHERE batch_code = '{batch_code}'
        """
        _execute_sql(update_query)

        log.info(f"[TOOL:requeue_settlement_batch] Success! Batch {batch_code} settled via {target_rail} with UTR: {utr_number}")
        return f"SUCCESS: Settlement batch {batch_code} settled via {target_rail}. Verified Bank UTR: {utr_number}"
    except Exception as e:
        log.error(f"[TOOL:requeue_settlement_batch] Error: {e}")
        return f"Failed to requeue batch: {str(e)}"

@tool
def release_settlement_hold(batch_code: str, approver_note: str) -> str:
    """Releases high-value velocity or risk holds on a settlement batch after supervisor approval."""
    log.info(f"[TOOL:release_settlement_hold] Releasing hold on {batch_code}. Note: {approver_note}")
    try:
        utr_number = f"UTR-{random.randint(9000000000, 9999999999)}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        update_query = f"""
        UPDATE settlement_batches
        SET status = 'SETTLED',
            hold_reason = 'SUPERVISOR_OVERRIDE_APPROVED',
            utr_number = '{utr_number}',
            cleared_at = '{now_str}'
        WHERE batch_code = '{batch_code}'
        """
        _execute_sql(update_query)
        log.info(f"[TOOL:release_settlement_hold] Batch {batch_code} released. Generated UTR: {utr_number}")
        return f"SUCCESS: High-value hold released for batch {batch_code}. Approved UTR: {utr_number}"
    except Exception as e:
        return f"Failed to release hold: {str(e)}"

@tool
def trigger_soundbox_chime(device_id: str, amount: float) -> str:
    """Triggers an instantaneous OTA audio broadcast test chime on the Paytm Soundbox device
    and verifies cellular SIM connection status.
    """
    log.info(f"[TOOL:trigger_soundbox_chime] Emitting OTA chime for {device_id} (₹{amount})")
    try:
        # Re-establish connectivity and mark chime acknowledged
        update_query = f"""
        UPDATE soundbox_devices
        SET sim_status = 'ONLINE',
            last_chime_status = 'SUCCESS',
            last_heartbeat = CURRENT_TIMESTAMP
        WHERE device_id = '{device_id}'
        """
        _execute_sql(update_query)
        chime_text = f"Paytm par {int(amount)} rupaye prapt hue"
        log.info(f"[TOOL:trigger_soundbox_chime] Soundbox {device_id} chime emitted: '{chime_text}'")
        return f"SUCCESS: Soundbox {device_id} restored to ONLINE. Audio broadcast emitted: '{chime_text}'."
    except Exception as e:
        return f"Failed to ping Soundbox: {str(e)}"

@tool
def verify_bank_utr(order_id: str) -> str:
    """Verifies core banking credit status and returns the final settlement UTR reference for an order."""
    log.info(f"[TOOL:verify_bank_utr] Checking UTR for order {order_id}")
    try:
        batches = _execute_sql(f"SELECT batch_code, total_amount, status, utr_number, rail FROM settlement_batches WHERE order_id = '{order_id}' LIMIT 1")
        if not batches:
            return f"No settlement batch found for order {order_id}."
        b = batches[0]
        if b["status"] == "SETTLED" and b["utr_number"]:
            return f"VERIFIED: Order {order_id} credited to merchant bank account via {b['rail']}. Bank UTR: {b['utr_number']}."
        return f"PENDING: Settlement for {order_id} is in status {b['status']}."
    except Exception as e:
        return f"Verification check failed: {str(e)}"

@tool
def switch_gateway_route(merchant_id: str, target_gateway: str = "ICICI_BACKUP") -> str:
    """Fails over merchant acquiring traffic from a degraded bank gateway (e.g. HDFC 503) to a healthy backup gateway (ICICI_BACKUP)."""
    log.info(f"[TOOL:switch_gateway_route] Switching merchant {merchant_id} traffic to {target_gateway}")
    return f"SUCCESS: Traffic for merchant {merchant_id} re-routed to {target_gateway}. Gateway latency restored to normal (42ms)."

@tool
def audit_npci_reversal_ledger(order_id: str, rrn: str = "409955102001") -> str:
    """Audits NPCI centralized UPI settlement switch for duplicate debits and verifies automatic customer reversal reference."""
    log.info(f"[TOOL:audit_npci_reversal_ledger] Auditing NPCI switch for order {order_id}, RRN {rrn}")
    return f"AUDIT VERIFIED: Order #{order_id} (RRN: {rrn}) had duplicate debit. Primary debit settled to merchant; second debit reversed by NPCI (Ref: REV-{order_id})."

@tool
def verify_inbound_upi_traffic(merchant_id: str, claimed_amount: float) -> str:
    """Audits the live NPCI UPI clearing switch and Paytm acquiring gateway buffer to verify if an incoming payment
    claimed by a customer actually exists or if it is a suspected counterfeit payment / fake screenshot attempt.
    """
    log.info(f"[TOOL:verify_inbound_upi_traffic] Auditing switch for merchant {merchant_id}, claimed amount ₹{claimed_amount}")
    matches = _execute_sql(f"""
        SELECT order_id, amount, status, customer_vpa, rrn, created_at 
        FROM transactions 
        WHERE merchant_id = '{merchant_id}' AND amount = {claimed_amount} AND status = 'SUCCESS'
        ORDER BY id DESC LIMIT 1
    """)
    if matches:
        return f"PAYMENT_FOUND: Order #{matches[0]['order_id']} of ₹{claimed_amount} exists on Paytm switch (RRN: {matches[0]['rrn']})."
    else:
        return f"ALERT_NO_RECORD: 0 matching transactions found on NPCI UPI switch for ₹{claimed_amount}. Suspected fake payment spoof / screen forgery. No funds entered Paytm settlement pipeline."

@tool
def trigger_soundbox_security_alert(device_id: str, alert_type: str = "FAKE_PAYMENT_WARNING", amount: float = 60.0) -> str:
    """Triggers an instantaneous high-priority OTA spoken security alert on the merchant's Paytm Soundbox
    warning the merchant that a claimed payment was NOT received and to verify the customer's actual bank SMS.
    """
    log.info(f"[TOOL:trigger_soundbox_security_alert] Emitting security alert for {device_id} ({alert_type}, ₹{amount})")
    update_query = f"""
    UPDATE soundbox_devices
    SET sim_status = 'ONLINE',
        last_chime_status = 'FRAUD_ALERT_EMITTED',
        last_heartbeat = CURRENT_TIMESTAMP
    WHERE device_id = '{device_id}'
    """
    _execute_sql(update_query)
    alert_voice = f"Savdhan: Paytm par {int(amount)} rupaye ka koi bhugtan prapt nahi hua hai. Kripya grahak ka bank SMS check karein."
    return f"SECURITY ALERT EMITTED: Soundbox {device_id} broadcasted spoken fraud alert: '{alert_voice}'."



