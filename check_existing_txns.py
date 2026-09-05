import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
db_url = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("SELECT id, merchant_id, customer_id, amount, status, created_at FROM transactions;")
rows = cur.fetchall()
print(f"Total transactions in database: {len(rows)}", flush=True)
for r in rows:
    print(f"  ID: {r[0]}, Merchant: {r[1]}, Customer: {r[2]}, Amount: {r[3]}, Status: {r[4]}, Created: {r[5]}", flush=True)

# Also check audit_log
cur.execute("SELECT id, merchant_id, action, transaction_id, created_at FROM audit_log;")
audit_rows = cur.fetchall()
print(f"Total audit_log entries: {len(audit_rows)}", flush=True)
for a in audit_rows:
    print(f"  ID: {a[0]}, Merchant: {a[1]}, Action: {a[2]}, TxnID: {a[3]}", flush=True)

cur.close()
conn.close()
