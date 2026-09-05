import React, { useState } from 'react'
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
  Clock,
  Terminal,
  Key,
  Shield,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight
} from 'lucide-react'

export default function Home() {
  const [activeSimScenario, setActiveSimScenario] = useState('approved')

  const scenarios = {
    approved: {
      title: 'Normal Grocery Purchase',
      agent: 'grocery_bot_v2',
      amount: '₹450.00',
      category: 'groceries',
      score: 0.12,
      verdict: 'APPROVED',
      verdictColor: '#34d399',
      drivers: ['Baseline spend frequency', 'Recognized merchant category'],
      gatewayAction: 'Razorpay Order generated automatically (ID: order_live_94827)',
      auditHash: '8f7a9b2c4e1d...3f2a'
    },
    held: {
      title: 'High-Ticket Electronics Spike',
      agent: 'procurement_agent',
      amount: '₹18,500.00',
      category: 'electronics',
      score: 0.58,
      verdict: 'HELD',
      verdictColor: '#fbbf24',
      drivers: ['Amount vs 7-day average ratio (4.2x)', 'Novel category for customer'],
      gatewayAction: 'Queued in Merchant Dashboard for Human Analyst 1-click Approval',
      auditHash: '3c8e1a9d7b4f...9e1c'
    },
    blocked: {
      title: 'Runaway Loop / Injection Attack',
      agent: 'autonomous_loop',
      amount: '₹95,000.00',
      category: 'luxury_crypto',
      score: 0.94,
      verdict: 'BLOCKED',
      verdictColor: '#f87171',
      drivers: ['Exceeds merchant max amount rule (₹50,000)', 'Velocity spike (> 10 req/min)'],
      gatewayAction: 'Checkout halted immediately; Claude AI plain-English reason attached',
      auditHash: '7a2f4c9e1b8d...5a3f'
    }
  }

  const currentSim = scenarios[activeSimScenario]

  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Ambient background glows */}
      <div className="glow-orb-indigo" style={{ top: '-180px', left: '15%' }} />
      <div className="glow-orb-purple" style={{ top: '800px', right: '5%' }} />
      <div className="glow-orb-rose" style={{ top: '2200px', left: '10%' }} />

      {/* HERO SECTION */}
      <section style={{ maxWidth: '1280px', margin: '0 auto', padding: '1.25rem 1.5rem 3.5rem', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        {/* GLOWING ORBITAL BADGE */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          margin: '0 auto 1.25rem'
        }}>
          <img
            src="/risk_layer_badge.png"
            alt="The Risk Layer for AI-Initiated Payments"
            style={{
              maxWidth: '540px',
              width: '90%',
              height: 'auto',
              display: 'block',
              mixBlendMode: 'screen',
              filter: 'drop-shadow(0 0 30px rgba(168, 85, 247, 0.45))'
            }}
          />
        </div>
        {/* 3D PIPELINE SHOWCASE */}
        <div style={{
          position: 'relative',
          maxWidth: '1100px',
          margin: '0 auto 2.5rem',
          borderRadius: '1.25rem',
          overflow: 'hidden',
          border: '1px solid rgba(168, 85, 247, 0.25)',
          boxShadow: '0 0 50px rgba(168, 85, 247, 0.15), 0 20px 40px rgba(0, 0, 0, 0.6)',
          background: 'radial-gradient(ellipse at center, rgba(168, 85, 247, 0.08) 0%, rgba(7, 10, 18, 0.95) 75%)'
        }}>
          <img
            src="/stitch_landing.png"
            alt="PayFilter Risk Decision Layer: Let AI Move Money. Not Risk."
            style={{
              width: '100%',
              height: 'auto',
              display: 'block',
              objectFit: 'contain'
            }}
          />
        </div>

        {/* CTA Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '4.5rem' }}>
          <Link to="/signup" className="btn-primary" style={{
            background: 'linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #c084fc 100%)',
            boxShadow: '0 0 25px rgba(168, 85, 247, 0.5)'
          }}>
            Get Started <ArrowRight size={18} />
          </Link>

          <Link
            to="/dashboard"
            className="btn-secondary"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(168, 85, 247, 0.3)'
            }}
          >
            Open Dashboard <ArrowRight size={15} color="#c084fc" />
          </Link>

          <Link to="/how-it-works" className="btn-secondary">
            <Cpu size={17} /> How It Works
          </Link>

          <Link to="/docs" className="btn-secondary" style={{ background: 'transparent' }}>
            <Terminal size={17} /> Developers & API
          </Link>
        </div>

        {/* INTERACTIVE RISK ENGINE SIMULATOR TERMINAL */}
        <div className="glass-panel" style={{ maxWidth: '1000px', margin: '0 auto 5rem', padding: '2rem', textAlign: 'left', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '1.25rem', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }} />
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#f59e0b' }} />
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10b981' }} />
              </div>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#c7d2fe', fontFamily: 'var(--font-mono)' }}>
                Live Decision Engine Simulator
              </span>
            </div>

            {/* Scenario Switcher Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.4)', padding: '4px', borderRadius: '10px' }}>
              <button
                onClick={() => setActiveSimScenario('approved')}
                style={{
                  padding: '0.4rem 0.85rem',
                  borderRadius: '7px',
                  border: 'none',
                  background: activeSimScenario === 'approved' ? 'rgba(16, 185, 129, 0.25)' : 'transparent',
                  color: activeSimScenario === 'approved' ? '#34d399' : '#94a3b8',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                1. Approved Flow
              </button>
              <button
                onClick={() => setActiveSimScenario('held')}
                style={{
                  padding: '0.4rem 0.85rem',
                  borderRadius: '7px',
                  border: 'none',
                  background: activeSimScenario === 'held' ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
                  color: activeSimScenario === 'held' ? '#fbbf24' : '#94a3b8',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                2. Held (Review) Flow
              </button>
              <button
                onClick={() => setActiveSimScenario('blocked')}
                style={{
                  padding: '0.4rem 0.85rem',
                  borderRadius: '7px',
                  border: 'none',
                  background: activeSimScenario === 'blocked' ? 'rgba(244, 63, 94, 0.25)' : 'transparent',
                  color: activeSimScenario === 'blocked' ? '#f87171' : '#94a3b8',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                3. Blocked Attack
              </button>
            </div>
          </div>

          {/* Simulator Body */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {/* Left: Input Payload */}
            <div style={{ background: 'rgba(0, 0, 0, 0.5)', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                Incoming Agent Payload
              </div>
              <div style={{ fontSize: '0.86rem', color: '#e2e8f0', lineHeight: 1.8 }}>
                <div><strong>Scenario:</strong> {currentSim.title}</div>
                <div><strong>Agent Type:</strong> <code style={{ color: '#c084fc' }}>{currentSim.agent}</code></div>
                <div><strong>Amount:</strong> <span style={{ color: '#38bdf8', fontWeight: 700 }}>{currentSim.amount}</span></div>
                <div><strong>Merchant Category:</strong> <code style={{ color: '#94a3b8' }}>{currentSim.category}</code></div>
                <div><strong>Pre-Payment Gateway:</strong> Razorpay Test Sandbox</div>
              </div>
            </div>

            {/* Right: Real-time Evaluation */}
            <div style={{ background: 'rgba(0, 0, 0, 0.5)', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>
                  Risk Verdict & Cryptographic Proof
                </span>
                <span style={{
                  padding: '0.2rem 0.65rem',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  fontWeight: 900,
                  background: `${currentSim.verdictColor}22`,
                  color: currentSim.verdictColor,
                  border: `1px solid ${currentSim.verdictColor}55`
                }}>
                  {currentSim.verdict}
                </span>
              </div>

              <div style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.7 }}>
                <div><strong>Model Anomaly Score:</strong> <span style={{ color: currentSim.verdictColor, fontWeight: 700 }}>{currentSim.score}</span> / 1.00</div>
                <div><strong>Trigger Drivers:</strong> {currentSim.drivers.join(', ')}</div>
                <div style={{ marginTop: '0.4rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                  <strong>Action:</strong> {currentSim.gatewayAction}
                </div>
                <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  Audit SHA-256: {currentSim.auditHash}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* KEY HIGHLIGHT STATS */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem',
          maxWidth: '1100px',
          margin: '0 auto 6rem'
        }}>
          <div className="glass-panel" style={{ padding: '1.75rem', textAlign: 'left' }}>
            <div style={{ color: '#818cf8', fontSize: '2.25rem', fontWeight: 900 }}>&lt; 90ms</div>
            <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>P99 Inference Latency</div>
            <div style={{ color: '#64748b', fontSize: '0.85rem' }}>Deterministic rules + IsolationForest</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.75rem', textAlign: 'left' }}>
            <div style={{ color: '#34d399', fontSize: '2.25rem', fontWeight: 900 }}>96.4%</div>
            <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>Precision Rate</div>
            <div style={{ color: '#64748b', fontSize: '0.85rem' }}>2.1% low false positive baseline</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.75rem', textAlign: 'left' }}>
            <div style={{ color: '#fbbf24', fontSize: '2.25rem', fontWeight: 900 }}>SHA-256</div>
            <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>Chained Audit Log</div>
            <div style={{ color: '#64748b', fontSize: '0.85rem' }}>100% tamper-evident auditability</div>
          </div>

          <div className="glass-panel" style={{ padding: '1.75rem', textAlign: 'left' }}>
            <div style={{ color: '#f43f5e', fontSize: '2.25rem', fontWeight: 900 }}>2-Factor</div>
            <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1rem', marginTop: '0.25rem' }}>Step-Up Kill Switch</div>
            <div style={{ color: '#64748b', fontSize: '0.85rem' }}>Instant emergency merchant freeze</div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE DIAGRAM SECTION */}
      <section style={{ maxWidth: '1280px', margin: '0 auto 6rem', padding: '0 1.5rem' }}>
        <div className="glass-panel" style={{ padding: '3.5rem 2.5rem', position: 'relative' }}>
          <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
              System Flow
            </span>
            <h2 style={{ fontSize: '2.4rem', fontWeight: 900, marginTop: '0.5rem', letterSpacing: '-0.02em' }}>
              End-to-End Decision & Audit Pipeline
            </h2>
            <p style={{ color: '#94a3b8', maxWidth: '650px', margin: '0.5rem auto 0', fontSize: '1rem' }}>
              How PayFilter evaluates each incoming autonomous AI transaction before Razorpay order generation.
            </p>
          </div>

          {/* Flow Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {/* Step 1 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  1
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Idempotency & Keys</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Authenticates merchant <code style={{ color: '#818cf8' }}>X-API-Key</code> via SHA-256 hash lookup and checks duplicate transaction IDs to prevent double scoring or replayed executions.
              </p>
            </div>

            {/* Step 2 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  2
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>10-D Feature Vector</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Leakage-safe rolling computation strictly prior to <code style={{ color: '#818cf8' }}>t_curr</code>: velocity bursts, spend ratios, novel merchant category flags, and hour deviations.
              </p>
            </div>

            {/* Step 3 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  3
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Rules + IsolationForest</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Deterministic limits check against merchant caps + cryptographically verified Isolation Forest model calculating normalized anomaly risk score [0.0 - 1.0].
              </p>
            </div>

            {/* Step 4 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  4
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>3-Tier Verdict</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Outputs <span style={{ color: '#34d399', fontWeight: 700 }}>Approved</span>, <span style={{ color: '#fbbf24', fontWeight: 700 }}>Held</span> (human confirmation / safe timeout), or <span style={{ color: '#f87171', fontWeight: 700 }}>Blocked</span> with clear machine drivers.
              </p>
            </div>

            {/* Step 5 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  5
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Chained Cryptography</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Every score, human review, and timeout writes to an append-only Postgres audit trail where row N hashes row N-1 for guaranteed tamper-proof integrity.
              </p>
            </div>

            {/* Step 6 */}
            <div className="glass-panel-interactive" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800 }}>
                  6
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Razorpay Order API</h3>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Approved transactions proceed with seamless Razorpay Order Creation without latency friction. Webhook signatures ensure end-to-end reconciliation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* THREE DECISION TIERS SHOWCASE */}
      <section style={{ maxWidth: '1280px', margin: '0 auto 6rem', padding: '0 1.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
          <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
            Decision Engine
          </span>
          <h2 style={{ fontSize: '2.4rem', fontWeight: 900, marginTop: '0.5rem', letterSpacing: '-0.02em' }}>
            Transparent 3-Tier Risk Classification
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.75rem' }}>
          {/* Approved */}
          <div className="glass-panel" style={{ padding: '2.25rem', borderTop: '4px solid #10b981' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <CheckCircle2 size={26} color="#10b981" />
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399' }}>Approved</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              Anomaly Score &lt; 0.45. Transaction fits established customer history baseline and passes all deterministic merchant limits.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '10px', fontSize: '0.85rem', color: '#cbd5e1' }}>
              <strong style={{ color: '#34d399' }}>Action:</strong> Instant proceed to payment gateway order generation.
            </div>
          </div>

          {/* Held */}
          <div className="glass-panel" style={{ padding: '2.25rem', borderTop: '4px solid #f59e0b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <AlertTriangle size={26} color="#f59e0b" />
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fbbf24' }}>Held</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              0.45 &le; Score &lt; 0.70. Moderate anomalous pattern or soft rule trigger. Queued for human analyst confirmation or safe auto-timeout.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '10px', fontSize: '0.85rem', color: '#cbd5e1' }}>
              <strong style={{ color: '#fbbf24' }}>Resolution:</strong> Analyst 1-click Approve/Deny with adaptive threshold feedback.
            </div>
          </div>

          {/* Blocked */}
          <div className="glass-panel" style={{ padding: '2.25rem', borderTop: '4px solid #f43f5e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <XCircle size={26} color="#f43f5e" />
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f87171' }}>Blocked</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              Score &ge; 0.70 or hard rule breach (exceeds order cap or velocity threshold). Instantly halted with Claude AI plain-English explanations.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.4)', padding: '1rem', borderRadius: '10px', fontSize: '0.85rem', color: '#cbd5e1' }}>
              <strong style={{ color: '#f87171' }}>Action:</strong> Order aborted before payment gateway; logged in audit chain.
            </div>
          </div>
        </div>
      </section>

      {/* DEVELOPER QUICKSTART INTEGRATION */}
      <section style={{ maxWidth: '1280px', margin: '0 auto 6rem', padding: '0 1.5rem' }}>
        <div className="glass-panel" style={{ padding: '3.5rem 2.5rem', background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 15, 30, 0.95) 100%)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2.5rem', alignItems: 'center' }}>
            <div>
              <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em' }}>
                Developer Quickstart
              </span>
              <h2 style={{ fontSize: '2.2rem', fontWeight: 900, marginTop: '0.5rem', letterSpacing: '-0.02em' }}>
                Integrate in 3 Lines of Code
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '1rem', marginTop: '1rem', lineHeight: 1.7 }}>
                Send a single pre-checkout HTTP POST to PayFilter with the AI agent transaction telemetry.
                Receive instantaneous deterministic risk scoring and Razorpay order validation.
              </p>

              <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <Link to="/docs" className="btn-primary" style={{ padding: '0.75rem 1.4rem', fontSize: '0.9rem' }}>
                  <Terminal size={16} /> View API Documentation
                </Link>
                <Link to="/signup" className="btn-secondary" style={{ padding: '0.75rem 1.4rem', fontSize: '0.9rem' }}>
                  <Key size={16} /> Generate API Key
                </Link>
              </div>
            </div>

            {/* Code Block Window */}
            <div style={{ background: '#070a12', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.1)', overflow: 'hidden' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
                <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '0.5rem', fontFamily: 'var(--font-mono)' }}>
                  POST /transactions/check
                </span>
              </div>
              <pre style={{ padding: '1.25rem', fontSize: '0.82rem', color: '#cbd5e1', overflowX: 'auto', lineHeight: 1.65 }}>
                <span style={{ color: '#a855f7' }}>curl</span> -X POST http://localhost:8000/transactions/check \<br />
                &nbsp;&nbsp;-H <span style={{ color: '#38bdf8' }}>"X-API-Key: pf_live_your_merchant_key"</span> \<br />
                &nbsp;&nbsp;-H <span style={{ color: '#38bdf8' }}>"Content-Type: application/json"</span> \<br />
                &nbsp;&nbsp;-d <span style={{ color: '#34d399' }}>'&#123;</span><br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"transaction_id"</span>: <span style={{ color: '#fde047' }}>"txn_98471"</span>,<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"merchant_id"</span>: <span style={{ color: '#fde047' }}>"merchant_acme_01"</span>,<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"customer_id"</span>: <span style={{ color: '#fde047' }}>"cust_alice_44"</span>,<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"amount"</span>: <span style={{ color: '#f97316' }}>450.00</span>,<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"merchant_category"</span>: <span style={{ color: '#fde047' }}>"groceries"</span>,<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: '#94a3b8' }}>"agent_type"</span>: <span style={{ color: '#fde047' }}>"autonomous_shopper"</span><br />
                &nbsp;&nbsp;<span style={{ color: '#34d399' }}>&#125;'</span>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CALL TO ACTION */}
      <section style={{ maxWidth: '1000px', margin: '0 auto 7rem', padding: '0 1.5rem', textAlign: 'center' }}>
        <div className="glass-panel" style={{ padding: '4rem 2rem', background: 'radial-gradient(circle at center, rgba(99, 102, 241, 0.15) 0%, rgba(15, 23, 42, 0.8) 100%)', border: '1px solid rgba(99, 102, 241, 0.35)' }}>
          <h2 style={{ fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 900, marginBottom: '1rem', letterSpacing: '-0.02em' }}>
            Ready to Secure Your Agentic Payment Flows?
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto 2.5rem' }}>
            Create a merchant sandbox key in seconds and test pre-payment risk scoring against autonomous AI loops.
          </p>
          <Link to="/signup" className="btn-primary" style={{ padding: '1rem 2.25rem', fontSize: '1.05rem' }}>
            Get Started with PayFilter <ArrowRight size={20} />
          </Link>
        </div>
      </section>
    </div>
  )
}
