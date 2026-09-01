import React, { useState } from 'react'
import { Terminal, Copy, Check, BookOpen, Key, AlertCircle } from 'lucide-react'

export default function Docs() {
  const [copiedCurl, setCopiedCurl] = useState(false)
  const [copiedPython, setCopiedPython] = useState(false)

  const curlExample = `curl -X POST http://localhost:8000/transactions/check \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: pf_live_your_merchant_api_key_here" \\
  -d '{
    "transaction_id": "4f18d7b8-3a9b-449e-b2d2-8b4317156911",
    "merchant_id": "a0000000-0000-0000-0000-000000000001",
    "customer_id": "cust_alice",
    "amount": 2450.00,
    "timestamp": "2026-09-01T12:00:00Z",
    "merchant_category": "electronics",
    "agent_type": "procurement_agent"
  }'`

  const pythonExample = `import httpx

API_KEY = "pf_live_your_merchant_api_key_here"
PAYFILTER_URL = "http://localhost:8000/transactions/check"

payload = {
    "transaction_id": "4f18d7b8-3a9b-449e-b2d2-8b4317156911",
    "merchant_id": "a0000000-0000-0000-0000-000000000001",
    "customer_id": "cust_alice",
    "amount": 2450.00,
    "timestamp": "2026-09-01T12:00:00Z",
    "merchant_category": "electronics",
    "agent_type": "procurement_agent",
}

response = httpx.post(
    PAYFILTER_URL,
    json=payload,
    headers={"X-API-Key": API_KEY}
)

decision = response.json()
if decision["status"] == "approved":
    # Safe to proceed with Razorpay Order Creation
    create_razorpay_order(amount=payload["amount"])
elif decision["status"] == "held":
    # Wait for human review or webhook notification
    notify_analyst_review(decision["transaction_id"])
else:
    # Abort order
    raise Exception(f"Transaction blocked: {decision['reason']['primary_driver']}")`

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text)
    if (type === 'curl') {
      setCopiedCurl(true)
      setTimeout(() => setCopiedCurl(false), 2000)
    } else {
      setCopiedPython(true)
      setTimeout(() => setCopiedPython(false), 2000)
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '4rem 1.5rem 6rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          <BookOpen size={16} /> Developer Documentation
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginTop: '0.5rem', marginBottom: '0.75rem' }}>
          API Integration Guide
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '1rem', lineHeight: 1.6 }}>
          Learn how to invoke PayFilter before initiating checkout payment workflows.
        </p>
      </div>

      {/* Authentication Banner */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2.5rem', borderLeft: '4px solid #6366f1' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Key size={18} color="#818cf8" />
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Merchant API Key Authentication</h3>
        </div>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
          Pass your API key in the <code style={{ color: '#a5b4fc', background: 'rgba(0,0,0,0.4)', padding: '0.15rem 0.35rem', borderRadius: '4px' }}>X-API-Key</code> request header.
          Keys are single-reveal upon merchant signup and hashed using SHA-256 on the backend.
        </p>
      </div>

      {/* Endpoint Spec */}
      <div style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 800, marginBottom: '1rem' }}>
          POST /transactions/check
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Evaluates an autonomous transaction against merchant rules and ML anomaly isolation models in sub-100ms.
        </p>

        {/* cURL Snippet */}
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Terminal size={14} /> cURL Example
            </span>
            <button
              onClick={() => handleCopy(curlExample, 'curl')}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                padding: '0.35rem 0.65rem',
                color: '#cbd5e1',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem'
              }}
            >
              {copiedCurl ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
              {copiedCurl ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre style={{
            background: 'rgba(0, 0, 0, 0.5)',
            padding: '1rem',
            borderRadius: '8px',
            fontSize: '0.8rem',
            color: '#e2e8f0',
            overflowX: 'auto',
            lineHeight: 1.5
          }}>
            <code>{curlExample}</code>
          </pre>
        </div>

        {/* Python Snippet */}
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Terminal size={14} /> Python (httpx) SDK Pattern
            </span>
            <button
              onClick={() => handleCopy(pythonExample, 'python')}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                padding: '0.35rem 0.65rem',
                color: '#cbd5e1',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem'
              }}
            >
              {copiedPython ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
              {copiedPython ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre style={{
            background: 'rgba(0, 0, 0, 0.5)',
            padding: '1rem',
            borderRadius: '8px',
            fontSize: '0.8rem',
            color: '#e2e8f0',
            overflowX: 'auto',
            lineHeight: 1.5
          }}>
            <code>{pythonExample}</code>
          </pre>
        </div>

        {/* Response Format Table */}
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem' }}>
          Response Payload Fields
        </h3>
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                <th style={{ padding: '0.85rem 1rem', color: '#f8fafc' }}>Field</th>
                <th style={{ padding: '0.85rem 1rem', color: '#f8fafc' }}>Type</th>
                <th style={{ padding: '0.85rem 1rem', color: '#f8fafc' }}>Description</th>
              </tr>
            </thead>
            <tbody style={{ color: '#94a3b8' }}>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '0.85rem 1rem', color: '#818cf8', fontFamily: 'var(--font-mono)' }}>status</td>
                <td style={{ padding: '0.85rem 1rem' }}>string</td>
                <td style={{ padding: '0.85rem 1rem' }}><code>"approved"</code> | <code>"held"</code> | <code>"blocked"</code></td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '0.85rem 1rem', color: '#818cf8', fontFamily: 'var(--font-mono)' }}>risk_score</td>
                <td style={{ padding: '0.85rem 1rem' }}>float</td>
                <td style={{ padding: '0.85rem 1rem' }}>Normalized anomaly probability [0.0 - 1.0]</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '0.85rem 1rem', color: '#818cf8', fontFamily: 'var(--font-mono)' }}>reason</td>
                <td style={{ padding: '0.85rem 1rem' }}>object</td>
                <td style={{ padding: '0.85rem 1rem' }}>Structured machine-readable drivers (e.g., burst velocity, ratio)</td>
              </tr>
              <tr>
                <td style={{ padding: '0.85rem 1rem', color: '#818cf8', fontFamily: 'var(--font-mono)' }}>audit_log_id</td>
                <td style={{ padding: '0.85rem 1rem' }}>UUID</td>
                <td style={{ padding: '0.85rem 1rem' }}>Cryptographic hash-chained audit record pointer</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
