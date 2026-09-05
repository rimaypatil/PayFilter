import os
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Set logging level to INFO to see [DB] logs
logging.basicConfig(level=logging.INFO)
load_dotenv("backend/.env")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.client import get_supabase_client
from backend.app.db.repository.merchants_repo import MerchantsRepository
from backend.app.auth.jwt_verify import create_mock_jwt

client = TestClient(app)
sb_client = get_supabase_client()
merchants_repo = MerchantsRepository(sb_client)

print("--- PAYFILTER REAL TRANSACTION INTEGRATION CHECK ---", flush=True)

merchant_id = "bb7e05c0-0463-48a1-baa2-5f424f6490cc"
user_id = "7591d775-2d9e-43b7-b8f7-9577067a4b5f"

# Rotate / get a live API key for this merchant
api_key = merchants_repo.rotate_api_key(merchant_id)
print(f"API key active for merchant {merchant_id}", flush=True)

# 1. Test POST /transactions/check
txn_id = str(uuid.uuid4())
customer_id = f"cust_live_{uuid.uuid4().hex[:6]}"
now_iso = datetime.now(timezone.utc).isoformat()

payload = {
    "transaction_id": txn_id,
    "merchant_id": merchant_id,
    "customer_id": customer_id,
    "amount": 550.00,
    "timestamp": now_iso,
    "merchant_category": "electronics",
    "agent_type": "procurement_bot",
}

print(f"\n[A] Sending POST /transactions/check for txn_id={txn_id}...", flush=True)
res_check = client.post("/transactions/check", json=payload, headers={"X-API-Key": api_key})
print(f"POST /transactions/check status: {res_check.status_code}", flush=True)
assert res_check.status_code == 200, f"Failed: {res_check.text}"
data = res_check.json()
print("Response data:", data, flush=True)

# 2. Verify response fields
assert data["transaction_id"] == txn_id
assert data["status"] in ["approved", "held", "blocked"]
assert data["risk_score"] is not None
assert data["audit_log_id"] is not None
print("[B] Response contains real transaction_id, risk_score, decision, and audit information: PASSED", flush=True)

# 3. Verify real record directly in Supabase
print(f"\n[C] Verifying transaction {txn_id} directly in Supabase...", flush=True)
db_res = sb_client.table("transactions").select("*").eq("id", txn_id).execute()
assert len(db_res.data) == 1, f"Expected 1 row in Supabase, got {db_res.data}"
db_row = db_res.data[0]
print(f"Direct Supabase row: id={db_row['id']}, amount={db_row['amount']}, status={db_row['status']}", flush=True)
assert db_row["merchant_id"] == merchant_id

# Verify audit log in Supabase
audit_res = sb_client.table("audit_log").select("*").eq("transaction_id", txn_id).execute()
print(f"Direct Supabase audit entries: {len(audit_res.data)}", flush=True)
assert len(audit_res.data) >= 1

# 4. Verify GET /transactions returns the newly created transaction
print(f"\n[D] Verifying GET /transactions with Admin JWT...", flush=True)
# Create valid Supabase JWT for this user & merchant
admin_jwt = create_mock_jwt(user_id=user_id, merchant_id=merchant_id, role="admin")

res_list = client.get(
    "/transactions?page=1&page_size=50",
    headers={"Authorization": f"Bearer {admin_jwt}"},
)
print(f"GET /transactions status: {res_list.status_code}", flush=True)
assert res_list.status_code == 200, f"Failed: {res_list.text}"
list_data = res_list.json()
print(f"GET /transactions items count: {len(list_data.get('items', []))}, total: {list_data.get('total')}", flush=True)

matching_items = [it for it in list_data.get("items", []) if it["id"] == txn_id]
assert len(matching_items) == 1, f"Transaction {txn_id} not found in GET /transactions response!"
print(f"[E] GET /transactions found newly created transaction: {matching_items[0]['id']}: PASSED", flush=True)

print("\nALL REAL SUPABASE TRANSACTION VERIFICATIONS PASSED SUCCESSFULLY!", flush=True)
