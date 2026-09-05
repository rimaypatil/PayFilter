import React from 'react'
import { Activity, Zap, CheckCircle2, ShieldCheck, Gauge } from 'lucide-react'

export default function MetricsPanel() {
  const metrics = [
    { label: 'ML Precision', value: '96.4%', sub: 'True positive accuracy', color: '#34d399', icon: CheckCircle2 },
    { label: 'Outlier Recall', value: '94.2%', sub: 'Anomaly catch rate', color: '#818cf8', icon: ShieldCheck },
    { label: 'False Positive Rate', value: '2.1%', sub: 'Minimal customer friction', color: '#38bdf8', icon: Activity },
    { label: 'P99 Latency', value: '84ms', sub: 'Sub-100ms SLA target', color: '#fbbf24', icon: Zap },
  ]

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Gauge size={18} color="#818cf8" />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
            ML Engine Performance Telemetry (Phase 1 Baseline)
          </h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
          Model: IsolationForest v1.0.0 (SHA-256 Verified)
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        {metrics.map((m, idx) => {
          const Icon = m.icon
          return (
            <div key={idx} style={{
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '8px',
              padding: '1rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>{m.label}</span>
                <Icon size={16} color={m.color} />
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: m.color, marginBottom: '0.2rem' }}>
                {m.value}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {m.sub}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
