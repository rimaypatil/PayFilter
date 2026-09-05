import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv("backend/.env")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.client import get_supabase_client
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.auth.jwt_verify import create_mock_jwt

client = TestClient(app)
sb_client = get_supabase_client()
merchants_repo = MerchantsRepository(sb_client)

merchant_id = "bb7e05c0-0463-48a1-baa2-5f424f6490cc"
user_id = "7591d775-2d9e-43b7-b8f7-9577067a4b5f"
admin_jwt = create_mock_jwt(user_id=user_id, merchant_id=merchant_id, role="admin")

print("=== 1. VERIFY FRESH STATE (0 TRANSACTIONS) ===", flush=True)
res_empty = client.get("/transactions?page=1&page_size=50", headers={"Authorization": f"Bearer {admin_jwt}"})
assert res_empty.status_code == 200, f"Error: {res_empty.text}"
data_empty = res_empty.json()
items_empty = data_empty.get("items", [])
total_empty = data_empty.get("total", 0)
print(f"Items count: {len(items_empty)}, Total: {total_empty}", flush=True)
assert len(items_empty) == 0, f"Expected 0 items, got {len(items_empty)}"
assert total_empty == 0, f"Expected total 0, got {total_empty}"

# Calculate stats as frontend does
approved_empty = len([t for t in items_empty if t.get("status", "").lower() == "approved"])
held_empty = len([t for t in items_empty if t.get("status", "").lower() == "held"])
blocked_empty = len([t for t in items_empty if t.get("status", "").lower() == "blocked"])
rate_empty = f"{(approved_empty / len(items_empty) * 100):.1f}" if len(items_empty) > 0 else "0.0"

print(f"Stats -> Total: {len(items_empty)}, Approved: {approved_empty}, Held: {held_empty}, Blocked: {blocked_empty}, Rate: {rate_empty}%", flush=True)
assert len(items_empty) == 0
assert rate_empty == "0.0"
assert held_empty == 0
assert blocked_empty == 0
print("FRESH ZERO STATE VERIFIED SUCCESSFULLY!\n", flush=True)

print("=== 2. INCOMING TRANSACTION CREATION ===", flush=True)
api_key = merchants_repo.rotate_api_key(merchant_id)
txn_id = str(uuid.uuid4())
customer_id = f"cust_demo_{uuid.uuid4().hex[:6]}"

payload = {
    "transaction_id": txn_id,
    "merchant_id": merchant_id,
    "customer_id": customer_id,
    "amount": 750.00,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "merchant_category": "electronics",
    "agent_type": "shopping_bot",
}

res_post = client.post("/transactions/check", json=payload, headers={"X-API-Key": api_key})
assert res_post.status_code == 200, f"Check failed: {res_post.text}"
post_data = res_post.json()
print("POST /transactions/check response:", post_data, flush=True)
assert post_data["transaction_id"] == txn_id

print("\n=== 3. VERIFY DASHBOARD SEES EXACTLY 1 TRANSACTION ===", flush=True)
res_one = client.get("/transactions?page=1&page_size=50", headers={"Authorization": f"Bearer {admin_jwt}"})
assert res_one.status_code == 200
data_one = res_one.json()
items_one = data_one.get("items", [])
total_one = data_one.get("total", 0)
print(f"Items count: {len(items_one)}, Total: {total_one}", flush=True)
assert len(items_one) == 1, f"Expected 1 item, got {len(items_one)}"
assert total_one == 1, f"Expected total 1, got {total_one}"
assert items_one[0]["id"] == txn_id
assert items_one[0]["amount"] == 750.00

approved_one = len([t for t in items_one if t.get("status", "").lower() == "approved"])
held_one = len([t for t in items_one if t.get("status", "").lower() == "held"])
blocked_one = len([t for t in items_one if t.get("status", "").lower() == "blocked"])
rate_one = f"{(approved_one / len(items_one) * 100):.1f}" if len(items_one) > 0 else "0.0"

print(f"Stats after 1 txn -> Total: {len(items_one)}, Approved: {approved_one}, Held: {held_one}, Blocked: {blocked_one}, Rate: {rate_one}%", flush=True)
assert len(items_one) == 1
assert rate_one == "100.0"
print("EXACTLY 1 TRANSACTION FLOW VERIFIED SUCCESSFULLY!", flush=True)
