# PayFilter — Video Demo & Live Walkthrough Script

This script outlines the exact sequence of screens, commands, and live interactions for demonstrating PayFilter in under 5 minutes.

---

## Pre-Demo Setup Checklist

1. Start Backend Server:
   ```bash
   uvicorn backend.app.main:app --port 8000 --reload
   ```
2. Start Landing Page:
   ```bash
   cd frontend/landing && npm run dev
   # Runs on http://localhost:3000
   ```
3. Start Dashboard:
   ```bash
   cd frontend/dashboard && npm run dev
   # Runs on http://localhost:3001
   ```

---

## Demo Sequence (Beat-by-Beat)

### Beat 1: The Pitch & Landing Page (0:00 – 0:45)
- **Screen**: Open `http://localhost:3000` (PayFilter Public Landing Page).
- **Spoken Key Point**: "Autonomous AI agents can purchase in milliseconds, but without a firewall, a prompt injection or runaway loop can drain merchant balances. PayFilter intercepts checkout requests before Razorpay order creation."
- **Action**: Scroll past the interactive 6-step architecture flow and key metrics (96.4% precision, &lt; 90ms latency). Click **How It Works** to briefly show the 3-tier decision matrix.

### Beat 2: Merchant Onboarding & Single-Reveal API Key (0:45 – 1:15)
- **Screen**: Navigate to `http://localhost:3000/signup`.
- **Action**: Enter Organization Name: `"Acme Procurement Corp"` and click **Generate API Key & Register**.
- **Visual Highlight**: Point out the prominent warning banner and copy the single-reveal API key (`pf_live_...`).
- **Spoken Key Point**: "API keys are shown only once and stored exclusively as SHA-256 digests on our backend."

### Beat 3: Clean Approve Path -> Real Razorpay Test Order (1:15 – 2:00)
- **Screen**: Navigate to `http://localhost:3001` (Dashboard) and log in.
- **Terminal Command**: Send a normal purchase request:
  ```bash
  curl -X POST http://localhost:8000/transactions/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <YOUR_MERCHANT_API_KEY>" \
    -d '{
      "transaction_id": "4f18d7b8-3a9b-449e-b2d2-8b4317156911",
      "merchant_id": "<YOUR_MERCHANT_ID>",
      "customer_id": "cust_demo_normal",
      "amount": 450.00,
      "timestamp": "2026-09-01T12:00:00Z",
      "merchant_category": "groceries",
      "agent_type": "grocery_bot"
    }'
  ```
- **Visual Highlight**: Show the instant **APPROVED** decision in the response containing a real Razorpay test order ID (`order_...`). Switch to the dashboard to show the transaction appear in the live feed.

### Beat 4: Hard Block & Claude Natural Language Explanation (2:00 – 2:45)
- **Terminal Command**: Submit a runaway velocity burst / massive order cap breach:
  ```bash
  curl -X POST http://localhost:8000/transactions/check \
    -H "Content-Type: application/json" \
    -H "X-API-Key: <YOUR_MERCHANT_API_KEY>" \
    -d '{
      "transaction_id": "8e29f8c9-4b1c-550f-c3e3-9c5428267022",
      "merchant_id": "<YOUR_MERCHANT_ID>",
      "customer_id": "cust_demo_burst",
      "amount": 89000.00,
      "timestamp": "2026-09-01T12:05:00Z",
      "merchant_category": "luxury_crypto",
      "agent_type": "runaway_loop"
    }'
  ```
- **Visual Highlight**: Point out that the transaction is **BLOCKED** with zero order created, and highlight the Claude-generated plain-English explanation:
  > *"This transaction represents a substantial ticket-size spike of ₹89,000.00 exceeding merchant limits."*
- **Spoken Key Point**: "Zero customer PII is sent to Claude — only numerical anomaly drivers."

### Beat 5: Human-in-the-Loop Confirmation Queue (2:45 – 3:30)
- **Screen**: Click **Flagged Queue** on the Dashboard (`http://localhost:3001/queue`).
- **Action**: Submit a borderline purchase (amount ₹4,800) that lands in the `held` review state.
- **Visual Highlight**: The card appears in real-time. Click **Approve**.
- **Result**: The transaction resolves instantly, receives a Razorpay order ID, updates the ML baseline threshold, and leaves the queue without a manual page reload.

### Beat 6: Cryptographic Audit Explorer (3:30 – 4:00)
- **Screen**: Click **Audit Trail** (`http://localhost:3001/audit`).
- **Visual Highlight**: Show the green **SHA-256 Chain Intact** badge. Walk through how every scoring decision, confirmation, and timeout hashes the previous row's digest ($H_n = \text{SHA256}(H_{n-1} \parallel \text{data})$).

### Beat 7: Two-Factor Step-Up Emergency Kill Switch (4:00 – 4:45)
- **Screen**: Click **Kill Switch** (`http://localhost:3001/kill-switch`) as Admin.
- **Action**: Click **Freeze All Agent Payments** -> receive short-lived 6-digit OTP code in dev banner -> enter code and confirm.
- **Visual Highlight**: The status flips to **ACTIVE (ALL PAYMENTS FROZEN)**.
- **Test**: Run any transaction check via curl -> observe immediate refusal (`status: "blocked"`, `primary_driver: "kill_switch_activated"`).

### Beat 8: Closing & Graceful Failure Summary (4:45 – 5:00)
- **Spoken Key Point**: "PayFilter protects autonomous AI commerce with sub-100ms latency, zero-PII Claude explanations, test-mode Razorpay automation, and tamper-evident cryptographic auditability."
