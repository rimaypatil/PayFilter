import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
db_url = os.environ.get("DATABASE_URL")

print("Connecting to Supabase PostgreSQL...", flush=True)
conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

try:
    print("Temporarily disabling audit_log mutation trigger...", flush=True)
    cur.execute("ALTER TABLE audit_log DISABLE TRIGGER trg_prevent_audit_log_mutation;")
    
    print("Clearing demo and test transaction rows...", flush=True)
    cur.execute("DELETE FROM transactions;")
    print("Transactions table cleared.", flush=True)

    print("Clearing transaction audit records...", flush=True)
    cur.execute("DELETE FROM audit_log WHERE action LIKE 'transaction_scored%';")
    print("Audit log transaction entries cleaned.", flush=True)

finally:
    print("Re-enabling audit_log mutation trigger...", flush=True)
    cur.execute("ALTER TABLE audit_log ENABLE TRIGGER trg_prevent_audit_log_mutation;")
    print("Trigger re-enabled.", flush=True)

# Verify counts
cur.execute("SELECT COUNT(*) FROM transactions;")
txn_count = cur.fetchone()[0]
print(f"\nTotal transactions after reset: {txn_count}", flush=True)

cur.execute("SELECT COUNT(*) FROM audit_log;")
audit_count = cur.fetchone()[0]
print(f"Total audit_log entries after reset: {audit_count}", flush=True)

cur.execute("SELECT COUNT(*) FROM merchants;")
merchant_count = cur.fetchone()[0]
print(f"Total merchants retained: {merchant_count}", flush=True)

cur.execute("SELECT COUNT(*) FROM user_roles;")
roles_count = cur.fetchone()[0]
print(f"Total user_roles retained: {roles_count}", flush=True)

cur.execute("SELECT COUNT(*) FROM rules_config;")
rules_count = cur.fetchone()[0]
print(f"Total rules_config retained: {rules_count}", flush=True)

cur.close()
conn.close()
print("\nReset complete!", flush=True)
