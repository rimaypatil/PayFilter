import React from 'react'
import { Shield, Lock, Terminal, Activity } from 'lucide-react'

export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      background: 'rgba(5, 8, 15, 0.95)',
      padding: '3rem 1.5rem 2rem',
      marginTop: '6rem'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '2.5rem',
          marginBottom: '3rem'
        }}>
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
              <div style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Shield size={16} color="#ffffff" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>PayFilter</span>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.6' }}>
              Real-time payment firewall & anomaly detection layer designed for autonomous AI agents prior to Razorpay order creation.
            </p>
          </div>

          {/* Security Architecture */}
          <div>
            <h4 style={{ color: '#f8fafc', fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Security Architecture
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem', color: '#94a3b8' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Lock size={14} color="#818cf8" /> SHA-256 Hash-Chained Audit Trail</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Shield size={14} color="#818cf8" /> Supabase Row-Level Security (RLS)</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Activity size={14} color="#818cf8" /> Adaptive Poisoning Defense Thresholds</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Terminal size={14} color="#818cf8" /> Step-Up Two-Factor Kill Switch</li>
            </ul>
          </div>

          {/* Decision Engine */}
          <div>
            <h4 style={{ color: '#f8fafc', fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Decision Tiers
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem', color: '#94a3b8' }}>
              <li><span style={{ color: '#34d399', fontWeight: 600 }}>Approved</span>: Low risk score (&lt; 0.45), instant proceed</li>
              <li><span style={{ color: '#fbbf24', fontWeight: 600 }}>Held</span>: Medium risk, analyst confirm / safe timeout</li>
              <li><span style={{ color: '#f87171', fontWeight: 600 }}>Blocked</span>: Hard rule breach / high anomaly score (&ge; 0.70)</li>
            </ul>
          </div>
        </div>

        <div style={{
          paddingTop: '2rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.8rem',
          color: '#64748b'
        }}>
          <div>© {new Date().getFullYear()} PayFilter AI. All rights reserved.</div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <span>Backend: FastAPI + Supabase Postgres</span>
            <span>ML: Scikit-Learn IsolationForest</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
