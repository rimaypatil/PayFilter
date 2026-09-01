import React from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldCheck,
  Zap,
  Lock,
  Activity,
  ArrowRight,
  Cpu,
  Database,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileCheck2,
  RefreshCw,
  Clock
} from 'lucide-react'

export default function Home() {
  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Background ambient glow */}
      <div className="glow-orb-indigo" style={{ top: '-150px', left: '20%' }} />
      <div className="glow-orb-rose" style={{ top: '600px', right: '10%' }} />

      {/* HERO SECTION */}
      <section style={{ maxWidth: '1200px', margin: '0 auto', padding: '5rem 1.5rem 4rem', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.85rem',
          borderRadius: '9999px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          color: '#a5b4fc',
          fontSize: '0.82rem',
          fontWeight: 600,
          marginBottom: '1.5rem'
        }}>
          <Cpu size={14} /> Built for Autonomous AI Agent Checkout Workflows
        </div>

        <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4.25rem)', fontWeight: 800, lineHeight: 1.15, letterSpacing: '-0.03em', marginBottom: '1.5rem' }}>
          Autonomous Agents Need a <br />
          <span className="gradient-text">Pre-Payment Firewall</span>
        </h1>

        <p style={{ maxWidth: '750px', margin: '0 auto 2.5rem', fontSize: '1.15rem', color: '#94a3b8', lineHeight: 1.6 }}>
          PayFilter intercepts autonomous AI agent checkout requests before Razorpay order creation.
          Evaluating burst velocity, ticket size anomalies, and novel categories using leakage-safe ML and immutable cryptographic audit trails.
        </p>

        {/* CTA Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '4rem' }}>
          <Link
            to="/signup"
            style={{
              padding: '0.85rem 1.85rem',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '1rem',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 10px 25px -5px rgba(99, 102, 241, 0.5)',
              transition: 'all 0.2s'
            }}
          >
            Create Merchant API Key <ArrowRight size={18} />
          </Link>

          <Link
            to="/how-it-works"
            style={{
              padding: '0.85rem 1.85rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#cbd5e1',
              fontWeight: 600,
              fontSize: '1rem',
              textDecoration: 'none',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s'
            }}
          >
            How It Works
          </Link>
        </div>

        {/* KEY HIGHLIGHT STATS */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem',
          maxWidth: '1000px',
          margin: '0 auto 5rem'
        }}>
          <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'left' }}>
            <div style={{ color: '#818cf8', fontSize: '2rem', fontWeight: 800 }}>&lt; 90ms</div>
            <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: '0.95rem' }}>P99 Inference Latency</div>
            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>Deterministic rules + IsolationForest</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'left' }}>
            <div style={{ color: '#34d399', fontSize: '2rem', fontWeight: 800 }}>96.4%</div>
            <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: '0.95rem' }}>Precision Rate</div>
            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>2.1% low false positive baseline</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'left' }}>
            <div style={{ color: '#fbbf24', fontSize: '2rem', fontWeight: 800 }}>SHA-256</div>
            <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: '0.95rem' }}>Chained Audit Log</div>
            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>100% tamper-evident auditability</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'left' }}>
            <div style={{ color: '#f43f5e', fontSize: '2rem', fontWeight: 800 }}>2-Factor</div>
            <div style={{ color: '#f8fafc', fontWeight: 600, fontSize: '0.95rem' }}>Step-Up Kill Switch</div>
            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>Instant emergency merchant freeze</div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE DIAGRAM SECTION */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem', padding: '0 1.5rem' }}>
        <div className="glass-panel" style={{ padding: '3rem 2rem', position: 'relative' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              System Flow
            </span>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, marginTop: '0.5rem' }}>
              End-to-End Decision & Audit Pipeline
            </h2>
            <p style={{ color: '#94a3b8', maxWidth: '600px', margin: '0.5rem auto 0', fontSize: '0.95rem' }}>
              How PayFilter evaluates each incoming autonomous transaction before order creation.
            </p>
          </div>

          {/* Flow Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {/* Step 1 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  1
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Idempotency & Keys</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Authenticates merchant <code style={{ color: '#818cf8' }}>X-API-Key</code> via SHA-256 hash lookup and checks duplicate transaction IDs to prevent double scoring.
              </p>
            </div>

            {/* Step 2 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  2
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>10-D Feature Vector</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Leakage-safe rolling computation strictly prior to <code style={{ color: '#818cf8' }}>t_curr</code>: velocity, ticket ratio, novel category flags, and hour deviation.
              </p>
            </div>

            {/* Step 3 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  3
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Rules + IsolationForest</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Deterministic limits check against merchant caps + cryptographically validated Isolation Forest model calculating normalized risk score [0.0 - 1.0].
              </p>
            </div>

            {/* Step 4 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  4
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>3-Tier Verdict</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Outputs <span style={{ color: '#34d399' }}>Approved</span>, <span style={{ color: '#fbbf24' }}>Held</span> (human confirmation / safe timeout), or <span style={{ color: '#f87171' }}>Blocked</span>.
              </p>
            </div>

            {/* Step 5 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  5
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Chained Cryptography</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Every score, human review, and timeout writes to an append-only Postgres audit trail where row N hashes row N-1 for guaranteed integrity.
              </p>
            </div>

            {/* Step 6 */}
            <div className="glass-panel-interactive" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                  6
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Razorpay Order API</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.5 }}>
                Approved transactions receive an authorization token to proceed with Razorpay Order Creation without latency friction.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* THREE DECISION TIERS SHOWCASE */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 6rem', padding: '0 1.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Decision Engine
          </span>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, marginTop: '0.5rem' }}>
            Transparent 3-Tier Risk Classification
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {/* Approved */}
          <div className="glass-panel" style={{ padding: '2rem', borderTop: '4px solid #10b981' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <CheckCircle2 size={24} color="#10b981" />
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#34d399' }}>Approved</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Score &lt; 0.45. Transaction fits established customer history baseline and passes all deterministic merchant caps.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: '#94a3b8' }}>
              <strong>Action:</strong> Instant proceed to payment gateway.
            </div>
          </div>

          {/* Held */}
          <div className="glass-panel" style={{ padding: '2rem', borderTop: '4px solid #f59e0b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <AlertTriangle size={24} color="#f59e0b" />
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fbbf24' }}>Held</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              0.45 &le; Score &lt; 0.70. Moderate anomalous pattern or soft rule trigger. Queued for human analyst approval or safe timeout.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: '#94a3b8' }}>
              <strong>Resolution:</strong> Analyst Approve/Deny or safe default.
            </div>
          </div>

          {/* Blocked */}
          <div className="glass-panel" style={{ padding: '2rem', borderTop: '4px solid #f43f5e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <XCircle size={24} color="#f43f5e" />
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f87171' }}>Blocked</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Score &ge; 0.70 or hard rule breach (exceeds order cap or velocity threshold). Instantly stopped with machine-readable drivers.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: '#94a3b8' }}>
              <strong>Action:</strong> Order aborted, recorded in audit log.
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
