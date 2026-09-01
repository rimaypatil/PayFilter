import React, { useState } from 'react'
import { Check, X, AlertTriangle, User, DollarSign, Bot, Clock, Tag } from 'lucide-react'
import RiskBadge from './RiskBadge'

export default function TransactionCard({ transaction, onConfirm }) {
  const [loadingAction, setLoadingAction] = useState(null)

  const handleAction = async (decision) => {
    setLoadingAction(decision)
    try {
      await onConfirm(transaction.id, decision)
    } finally {
      setLoadingAction(null)
    }
  }

  const reason = transaction.reason || {}
  const primaryDriver = reason.primary_driver || reason.rule_name || 'anomaly_detected'

  return (
    <div className="glass-card-interactive" style={{ padding: '1.5rem', marginBottom: '1rem', borderLeft: '4px solid #f59e0b' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
              ₹{Number(transaction.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
            <RiskBadge status={transaction.status} score={transaction.risk_score} />
          </div>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
            ID: {transaction.id}
          </div>
        </div>

        {/* Action Buttons for Held state */}
        {transaction.status === 'held' && (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => handleAction('approve')}
              disabled={loadingAction !== null}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                color: '#34d399',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: loadingAction ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Check size={16} /> {loadingAction === 'approve' ? 'Approving...' : 'Approve'}
            </button>

            <button
              onClick={() => handleAction('deny')}
              disabled={loadingAction !== null}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.4)',
                color: '#f87171',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: loadingAction ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <X size={16} /> {loadingAction === 'deny' ? 'Denying...' : 'Deny (Block)'}
            </button>
          </div>
        )}
      </div>

      {/* Transaction Details Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '0.75rem',
        background: 'rgba(0, 0, 0, 0.3)',
        padding: '0.85rem 1rem',
        borderRadius: '8px',
        fontSize: '0.82rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
          <User size={14} color="#818cf8" />
          <span>Customer: <strong>{transaction.customer_id}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
          <Bot size={14} color="#818cf8" />
          <span>Agent: <strong>{transaction.agent_type || 'autonomous'}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
          <AlertTriangle size={14} color="#fbbf24" />
          <span>Driver: <strong style={{ color: '#fde68a' }}>{primaryDriver}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#cbd5e1' }}>
          <Clock size={14} color="#818cf8" />
          <span>Time: <strong>{new Date(transaction.created_at || Date.now()).toLocaleTimeString()}</strong></span>
        </div>
      </div>
    </div>
  )
}
