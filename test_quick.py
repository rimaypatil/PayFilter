import os
os.environ["OMP_NUM_THREADS"] = "1"

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.client import reset_in_memory_db
from backend.app.risk_engine.model import get_model_manager

print("1. Initializing...", flush=True)
reset_in_memory_db()
get_model_manager().initialize()

print("2. Creating TestClient...", flush=True)
client = TestClient(app, raise_server_exceptions=True)

print("3. Calling /health...", flush=True)
res = client.get("/health")
print("Health:", res.status_code, res.json(), flush=True)

print("4. Calling /merchants/signup...", flush=True)
res2 = client.post("/merchants/signup", json={"name": "Test Acme", "admin_user_id": "u123"})
print("Signup:", res2.status_code, res2.json(), flush=True)
