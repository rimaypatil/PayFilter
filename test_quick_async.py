import os
os.environ["OMP_NUM_THREADS"] = "1"

import asyncio
import httpx
from backend.app.main import app
from backend.app.db.client import reset_in_memory_db
from backend.app.risk_engine.model import get_model_manager

async def main():
    print("1. Initializing...", flush=True)
    reset_in_memory_db()
    get_model_manager().initialize()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("2. Calling /health...", flush=True)
        res = await client.get("/health")
        print("Health:", res.status_code, res.json(), flush=True)

        print("3. Calling /merchants/signup...", flush=True)
        res2 = await client.post("/merchants/signup", json={"name": "Test Acme", "admin_user_id": "u123"})
        print("Signup:", res2.status_code, res2.json(), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
