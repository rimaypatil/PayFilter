import React, { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldCheck, UserCheck } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'
import TransactionCard from '../components/TransactionCard'

export default function FlaggedQueue({ onQueueChange }) {
  const authContext = useAuth()
  const [heldTransactions, setHeldTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionSuccess, setActionSuccess] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const loadQueue = async (isManual = false) => {
    if (!authContext.merchantId) return
    if (isManual) setRefreshing(true)
    try {
      const data = await api.getTransactions(authContext, 'held', 1, 50)
      const items = data?.items || []
      setHeldTransactions(items)
      if (onQueueChange) onQueueChange(items.length)
    } catch (err) {
      console.error('Failed to fetch held queue:', err)
    } finally {
      setLoading(false)
      if (isManual) setRefreshing(false)
    }
  }

  useEffect(() => {
    if (!authContext.loading && authContext.merchantId) {
      loadQueue()
      const interval = setInterval(loadQueue, 4000)
      return () => clearInterval(interval)
    } else if (!authContext.loading && !authContext.merchantId) {
      setLoading(false)
    }
  }, [authContext.merchantId, authContext.loading])

  const handleConfirmDecision = async (transactionId, decision) => {
    try {
      const res = await api.confirmTransaction(authContext, transactionId, decision)
      // Optimistically update list
      setHeldTransactions(prev => prev.filter(t => t.id !== transactionId))
      setActionSuccess({
        transactionId,
        decision,
        status: res.status,
        newThreshold: res.new_threshold,
      })
      if (onQueueChange) onQueueChange(heldTransactions.length - 1)
      setTimeout(() => setActionSuccess(null), 4000)
    } catch (err) {
      alert(`Confirmation failed: ${err.message || 'Error executing confirmation'}`)
    }
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <AlertTriangle size={24} color="#f59e0b" />
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
              Flagged Review Queue
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Transactions held for human risk assessment. Decisions dynamically adapt customer risk thresholds.
          </p>
        </div>

        <button
          onClick={() => loadQueue(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 0.85rem',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-subtle)',
            color: '#cbd5e1',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Refreshing...' : 'Refresh Queue'}
        </button>
      </div>

      {/* Success Notice Banner */}
      {actionSuccess && (
        <div style={{
          background: actionSuccess.decision === 'approve' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          border: `1px solid ${actionSuccess.decision === 'approve' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(244, 63, 94, 0.4)'}`,
          borderRadius: '8px',
          padding: '0.85rem 1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          fontSize: '0.85rem',
          color: actionSuccess.decision === 'approve' ? '#6ee7b7' : '#fca5a5'
        }}>
          <CheckCircle2 size={18} />
          <span>
            Transaction <strong>{actionSuccess.transactionId.substring(0, 13)}...</strong> successfully resolved to <strong>{actionSuccess.status.toUpperCase()}</strong>.
            (Updated ML Threshold: {actionSuccess.newThreshold})
          </span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '4rem 0', color: '#64748b' }}>
          Loading flagged queue...
        </div>
      )}

      {/* Empty State */}
      {!loading && heldTransactions.length === 0 && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem'
          }}>
            <ShieldCheck size={28} color="#10b981" />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.4rem' }}>
            Flagged Queue is Clear
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', maxWidth: '420px', margin: '0 auto' }}>
            No pending holds requiring analyst review. Incoming transactions with anomaly scores between 0.45 and 0.70 will appear here automatically.
          </p>
        </div>
      )}

      {/* Held Cards List */}
      {!loading && heldTransactions.length > 0 && (
        <div>
          {heldTransactions.map(txn => (
            <TransactionCard
              key={txn.id}
              transaction={txn}
              onConfirm={handleConfirmDecision}
            />
          ))}
        </div>
      )}
    </div>
  )
}
