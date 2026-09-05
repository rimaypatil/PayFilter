import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
db_url = os.environ.get("DATABASE_URL")
migrations_dir = Path("backend/app/db/migrations")

migration_files = [
    "0001_create_merchants.sql",
    "0002_create_transactions.sql",
    "0003_create_audit_log.sql",
    "0004_create_rules_config.sql",
    "0005_create_user_roles.sql",
    "0006_enable_rls.sql",
    "0007_rls_policies.sql",
    "0008_update_rls_for_auth.sql",
    "0009_add_razorpay_order_id.sql",
    "seed_demo_data.sql",
]

print("Connecting to Supabase PostgreSQL...", flush=True)
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

for fname in migration_files:
    fpath = migrations_dir / fname
    if not fpath.exists():
        print(f"Warning: {fname} not found!", flush=True)
        continue
    print(f"Applying migration: {fname}...", flush=True)
    sql = fpath.read_text(encoding="utf-8")
    try:
        cur.execute(sql)
        print(f"  Successfully applied {fname}", flush=True)
    except Exception as e:
        print(f"  Error applying {fname}: {type(e)} {e}", flush=True)

# Notify PostgREST to reload schema cache
print("Notifying PostgREST to reload schema cache...", flush=True)
try:
    cur.execute("NOTIFY pgrst, 'reload schema';")
    print("  Schema reload notification sent.", flush=True)
except Exception as e:
    print("  Error sending notify:", e, flush=True)

# Verify public tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = [row[0] for row in cur.fetchall()]
print(f"\nPublic tables after migrations ({len(tables)}): {tables}", flush=True)

cur.close()
conn.close()
print("Migrations complete!", flush=True)
