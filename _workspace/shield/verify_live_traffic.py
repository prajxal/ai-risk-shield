"""
Comprehensive Live Traffic & Return-Risk Shield Re-Verification Suite.
Validates:
1. Dynamic rate control (1x Normal @ 2000ms, 5x Turbo @ 250ms).
2. Strict namespace isolation (cust_live_*, ret_live_*).
3. Zero leakage of old checkout-shaped fields (checkout_payload, user_stated_intent, cart_items, shipping_address).
4. Concurrent rendering of Honest-Failure Spotlight (ret_synth_fail_001) during active live traffic.
"""
import time
import requests
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    print("=" * 70)
    print("1. HEALTH & DETECTOR VERIFICATION")
    print("=" * 70)
    health = requests.get(f"{BASE_URL}/health").json()
    print(f"Health Status: {health.get('status')} | Service: {health.get('service')}")
    print(f"Detector Active: {health.get('detector')}")
    assert health.get("shield_active") is True

    print("\n" + "=" * 70)
    print("2. START LIVE TRAFFIC AT 1X NORMAL (2000ms interval, 40% abuse ratio)")
    print("=" * 70)
    res_start = requests.post(f"{BASE_URL}/stream/start", json={"interval_ms": 2000, "attack_ratio": 0.4}).json()
    print(f"Stream Start Response: status={res_start.get('status')}, interval_ms={res_start.get('interval_ms')}")
    
    # Run 1x for 8 seconds
    print("Accumulating 1x live traffic for 8 seconds...")
    time.sleep(8.0)
    
    status_1x = requests.get(f"{BASE_URL}/stream/status").json()
    print(f"1x Status -> Total Events: {status_1x['total_generated_count']} "
          f"(Allowed: {status_1x['allowed_count']}, Flagged: {status_1x['flagged_count']}, Blocked: {status_1x['blocked_count']})")
    assert status_1x['total_generated_count'] >= 3

    print("\n" + "=" * 70)
    print("3. SHIFT TO 5X TURBO SPEED (250ms interval)")
    print("=" * 70)
    res_ctrl = requests.post(f"{BASE_URL}/stream/control", json={"interval_ms": 250}).json()
    print(f"Stream Control Response: interval_ms={res_ctrl.get('interval_ms')}")
    
    # Run 5x Turbo for 6 seconds (~24 events)
    print("Accumulating 5x Turbo traffic for 6 seconds...")
    time.sleep(6.0)
    
    status_5x = requests.get(f"{BASE_URL}/stream/status").json()
    print(f"5x Turbo Status -> Total Events: {status_5x['total_generated_count']} "
          f"(Allowed: {status_5x['allowed_count']}, Flagged: {status_5x['flagged_count']}, Blocked: {status_5x['blocked_count']})")
    assert status_5x['total_generated_count'] > status_1x['total_generated_count'] + 15

    print("\n" + "=" * 70)
    print("4. CONCURRENT HONEST-FAILURE SPOTLIGHT INTEGRITY CHECK")
    print("=" * 70)
    # Query /failure-case while live stream is actively running
    fail_case = requests.get(f"{BASE_URL}/failure-case").json()
    print(f"Failure Case ID: {fail_case.get('scenario_id')}")
    print(f"Attack Vector: {fail_case.get('attack_vector')}")
    print(f"Customer Profile: {fail_case.get('customer_profile_summary')}")
    print(f"Item: {fail_case.get('order_item')}")
    print(f"Ground Truth vs Actual: Expected {fail_case.get('ground_truth_decision')} -> Actual {fail_case.get('shield_actual_decision')}")
    assert fail_case.get("scenario_id") == "ret_synth_fail_001"
    assert fail_case.get("ground_truth_decision") == "FLAG"
    assert fail_case.get("shield_actual_decision") == "ALLOW"
    print("✓ Honest Failure Spotlight renders ret_synth_fail_001 correctly under live traffic load.")

    print("\n" + "=" * 70)
    print("5. STOP STREAM & AUDIT LOG INSPECTION")
    print("=" * 70)
    res_stop = requests.post(f"{BASE_URL}/stream/stop").json()
    print(f"Stream Stopped: is_running={res_stop.get('is_running')}")

    # Inspect audit logs
    audit_logs = requests.get(f"{BASE_URL}/audit-logs?limit=50").json()
    print(f"Fetched {len(audit_logs)} recent audit log records.")

    # Check isolation and field shapes
    old_fields_detected = []
    live_namespaces_valid = []
    
    forbidden_keys = ["checkout_payload", "user_stated_intent", "cart_items", "shipping_address", "max_budget"]

    for log in audit_logs:
        log_str = json.dumps(log)
        for key in forbidden_keys:
            if f'"{key}"' in log_str:
                old_fields_detected.append((log.get("audit_id"), key))

        # Check live namespace isolation
        ev_id = log.get("event_id") or log.get("transaction_id") or ""
        cust_id = log.get("customer_id") or log.get("agent_id") or ""
        if "live" in ev_id:
            assert ev_id.startswith("ret_live_"), f"Invalid event namespace: {ev_id}"
            assert cust_id.startswith("cust_live_"), f"Invalid customer namespace: {cust_id}"
            live_namespaces_valid.append(ev_id)

    print(f"Live Events Verified: {len(live_namespaces_valid)} matching 'ret_live_*' / 'cust_live_*'")
    print(f"Old Checkout Fields Leaked: {len(old_fields_detected)}")
    assert len(old_fields_detected) == 0, f"Found leaked checkout fields: {old_fields_detected}"
    print("✓ Zero old checkout fields leaked into live return events.")
    print("✓ Session and account namespaces are 100% strictly isolated.")

    print("\n" + "=" * 70)
    print("ALL 4 VERIFICATION CRITERIA PASSED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
