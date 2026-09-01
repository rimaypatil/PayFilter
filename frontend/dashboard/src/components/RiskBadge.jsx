import React from 'react'
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'

export default function RiskBadge({ status, score = null }) {
  const normalizedStatus = String(status || '').toLowerCase()

  if (normalizedStatus === 'approved') {
    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.2rem 0.6rem',
        borderRadius: '9999px',
        background: 'rgba(16, 185, 129, 0.15)',
        color: '#34d399',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        fontSize: '0.75rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.04em'
      }}>
        <CheckCircle2 size={13} /> Approved {score !== null && `(${(score * 100).toFixed(0)}%)`}
      </span>
    )
  }

  if (normalizedStatus === 'held') {
    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.2rem 0.6rem',
        borderRadius: '9999px',
        background: 'rgba(245, 158, 11, 0.15)',
        color: '#fbbf24',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        fontSize: '0.75rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.04em'
      }}>
        <AlertTriangle size={13} /> Held {score !== null && `(${(score * 100).toFixed(0)}%)`}
      </span>
    )
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.35rem',
      padding: '0.2rem 0.6rem',
      borderRadius: '9999px',
      background: 'rgba(244, 63, 94, 0.15)',
      color: '#f87171',
      border: '1px solid rgba(244, 63, 94, 0.3)',
      fontSize: '0.75rem',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.04em'
    }}>
      <XCircle size={13} /> Blocked {score !== null && `(${(score * 100).toFixed(0)}%)`}
    </span>
  )
}
