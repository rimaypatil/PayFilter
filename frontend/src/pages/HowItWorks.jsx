import React from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldAlert,
  Clock,
  UserCheck,
  Zap,
  TrendingUp,
  Cpu,
  Layers,
  Key,
  ShieldCheck,
  AlertOctagon,
  ArrowRight
} from 'lucide-react'

export default function HowItWorks() {
  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '4rem 1.5rem 6rem' }}>
      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
        <span style={{ color: '#818cf8', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Deep Dive
        </span>
        <h1 style={{ fontSize: 'clamp(2.2rem, 4vw, 3.5rem)', fontWeight: 800, marginTop: '0.5rem', marginBottom: '1rem' }}>
          How PayFilter Secures <span className="gradient-text">AI Commerce</span>
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '1.1rem', maxWidth: '650px', margin: '0 auto' }}>
          Autonomous AI agents execute actions in milliseconds. PayFilter provides the safety rails, anomaly detection, and human verification before real funds move.
        </p>
      </div>

      {/* SECTION 1: THE CORE PROBLEM */}
      <div className="glass-panel" style={{ padding: '2.5rem', marginBottom: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <ShieldAlert size={28} color="#f43f5e" />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>The Problem with Autonomous AI Agents</h2>
        </div>
        <p style={{ color: '#94a3b8', fontSize: '1rem', lineHeight: 1.7, marginBottom: '1rem' }}>
          Unlike human shoppers who browse, review cart totals, and confirm OTPs, autonomous LLM agents can loop, make hallucinated purchases, suffer runaway velocity bursts, or get hijacked via prompt injections.
        </p>
        <p style={{ color: '#94a3b8', fontSize: '1rem', lineHeight: 1.7 }}>
          If an autonomous agent is connected directly to a payment gateway, a single bug or injection can drain thousands of dollars in seconds before anyone notices.
        </p>
      </div>

      {/* SECTION 2: 5 ANOMALY DETECTION VECTORS */}
      <div style={{ marginBottom: '4rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '1.5rem', textAlign: 'center' }}>
          5 Anomaly Detection Vectors
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Zap size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>1. Burst Velocity</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Detects high-frequency loops (e.g., &gt; 5 transactions per minute) indicating runaway agent execution.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <TrendingUp size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>2. Ticket Size Spikes</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Identifies sudden purchases exceeding 3x–10x of the customer’s historical rolling average order value.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Layers size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>3. Novel Categories</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Flags first-time purchases in high-risk categories (e.g., luxury, crypto, gift cards) unseen in past history.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Clock size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>4. Temporal Deviations</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Calculates circular hour-of-day deviations to catch unusual off-peak automated shopping behavior.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <ShieldCheck size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>5. Poisoning Defense</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Adaptive thresholding with a hard 10% drift cap to prevent adversaries from gradually training the model to accept fraud.
            </p>
          </div>
        </div>
      </div>

      {/* SECTION 3: HUMAN CONFIRMATION & TIMEOUT SAFE DEFAULT */}
      <div className="glass-panel" style={{ padding: '2.5rem', marginBottom: '4rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <UserCheck size={28} color="#fbbf24" />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Human-in-the-Loop & Safe Timeouts</h2>
        </div>
        <p style={{ color: '#94a3b8', fontSize: '1rem', lineHeight: 1.7, marginBottom: '1.5rem' }}>
          When an anomaly is flagged as <strong style={{ color: '#fbbf24' }}>Held</strong>, it lands in the merchant’s Analyst Queue:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '10px' }}>
            <h4 style={{ color: '#34d399', fontWeight: 700, marginBottom: '0.5rem' }}>Analyst Approves</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Status updates to <code>approved</code>, authorization token generated, and outcome feeds the ML threshold manager.
            </p>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '10px' }}>
            <h4 style={{ color: '#f87171', fontWeight: 700, marginBottom: '0.5rem' }}>Analyst Denies</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Status updates to <code>blocked</code>, preventing order creation and recording confirmed fraud in the audit trail.
            </p>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '10px' }}>
            <h4 style={{ color: '#a5b4fc', fontWeight: 700, marginBottom: '0.5rem' }}>Unreviewed Timeout</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              If unreviewed after 120s: Large amounts (&gt; 25,000 INR) default safely to <strong>Blocked</strong>; low amounts to <strong>Approved</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center' }}>
        <Link
          to="/signup"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 2rem',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#ffffff',
            fontWeight: 700,
            textDecoration: 'none',
            fontSize: '1rem',
            boxShadow: '0 10px 25px -5px rgba(99, 102, 241, 0.5)'
          }}
        >
          Sign Up & Get API Key <ArrowRight size={18} />
        </Link>
      </div>
    </div>
  )
}
