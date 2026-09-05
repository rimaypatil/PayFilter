import React, { useState, useEffect } from 'react'
import { Activity, CheckCircle2, AlertTriangle, XCircle, RefreshCw, Layers, ArrowUpRight } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'
import MetricsPanel from '../components/MetricsPanel'
import RiskBadge from '../components/RiskBadge'

export default function Dashboard() {
  const authContext = useAuth()
  const { session, role, merchantId, merchantName, loading: authLoading } = authContext
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)

  const loadTransactions = async (isManual = false) => {
    if (!merchantId) return
    if (isManual) setRefreshing(true)
    setErrorMsg(null)
    try {
      const data = await api.getTransactions(authContext, filter, 1, 50)
      setTransactions(data?.items || [])
    } catch (err) {
      if (err.status === 403) {
        setErrorMsg('Access Restricted (403): You do not have permission to view this merchant tenant.')
      } else if (err.status === 401) {
        setErrorMsg('Session expired. Please re-authenticate.')
      } else {
        setErrorMsg(err.detail || err.message || 'Failed to load live transactions')
      }
    } finally {
      setLoading(false)
      if (isManual) setRefreshing(false)
    }
  }

  useEffect(() => {
    if (!authLoading && merchantId) {
      loadTransactions()
      const interval = setInterval(() => {
        loadTransactions()
      }, 5000)
      return () => clearInterval(interval)
    } else if (!authLoading && !merchantId) {
      setLoading(false)
    }
  }, [filter, merchantId, authLoading])

  if (authLoading) {
    return (
      <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#94a3b8' }}>
        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem', display: 'block', color: '#818cf8' }} />
        <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>Authenticating PayFilter session...</span>
      </div>
    )
  }

  if (role === 'unassigned' || !merchantId) {
    return (
      <div className="glass-card" style={{ maxWidth: '620px', margin: '4rem auto', padding: '2.5rem', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.75rem' }}>
          No Merchant Organization Assigned
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
          Your account is authenticated, but no active merchant organization was found in the database. Please register an organization to activate dashboard access.
        </p>
        <a
          href="/signup"
          style={{
            display: 'inline-block',
            padding: '0.75rem 1.5rem',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#fff',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 700,
            fontSize: '0.9rem'
          }}
        >
          Register Merchant Organization
        </a>
      </div>
    )
  }

  // Aggregate stats
  const totalCount = transactions.length
  const approvedCount = transactions.filter(t => t.status?.toLowerCase() === 'approved').length
  const heldCount = transactions.filter(t => t.status?.toLowerCase() === 'held').length
  const blockedCount = transactions.filter(t => t.status?.toLowerCase() === 'blocked').length
  const approvalRate = totalCount > 0 ? ((approvedCount / totalCount) * 100).toFixed(1) : '0.0'

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Live Risk Overview
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Monitoring AI agent checkout evaluations for merchant <code style={{ color: '#818cf8' }}>{authContext.merchantId}</code>
          </p>
        </div>

        <button
          onClick={() => loadTransactions(true)}
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
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* STAT COUNTER CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            <span>Total Evaluated</span>
            <Layers size={16} color="#818cf8" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            {totalCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
            Across all AI agent channels
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            <span>Approval Rate</span>
            <CheckCircle2 size={16} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399' }}>
            {approvalRate}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
            {approvedCount} orders passed instantly
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem', borderLeft: heldCount > 0 ? '3px solid #f59e0b' : '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            <span>Holds Pending</span>
            <AlertTriangle size={16} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fbbf24' }}>
            {heldCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
            Awaiting human analyst confirmation
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            <span>Blocked Orders</span>
            <XCircle size={16} color="#f43f5e" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f87171' }}>
            {blockedCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
            High-risk / hard limit breaches
          </div>
        </div>
      </div>

      {/* METRICS PANEL */}
      <MetricsPanel />

      {/* LIVE TRANSACTIONS TABLE */}
      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>Recent Transactions Feed</h2>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Live polling every 5 seconds</span>
          </div>

          {/* Status Filter Buttons */}
          <div style={{ display: 'flex', gap: '0.4rem', background: 'rgba(0,0,0,0.4)', padding: '0.25rem', borderRadius: '8px' }}>
            {[
              { label: 'All', val: null },
              { label: 'Approved', val: 'approved' },
              { label: 'Held', val: 'held' },
              { label: 'Blocked', val: 'blocked' },
            ].map(tab => (
              <button
                key={tab.label}
                onClick={() => setFilter(tab.val)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  border: 'none',
                  background: filter === tab.val ? '#6366f1' : 'transparent',
                  color: filter === tab.val ? '#ffffff' : '#94a3b8',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: '#64748b', fontSize: '0.9rem' }}>
            Loading transactions...
          </div>
        )}

        {/* Empty State */}
        {!loading && transactions.length === 0 && (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: '#64748b' }}>
            <Layers size={36} color="#334155" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ color: '#cbd5e1', fontSize: '1rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              No Transactions Recorded
            </h3>
            <p style={{ fontSize: '0.8rem', maxWidth: '380px', margin: '0 auto' }}>
              Invoke <code>POST /transactions/check</code> with your API key to see real-time payment evaluations stream in.
            </p>
          </div>
        )}

        {/* Table List */}
        {!loading && transactions.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Transaction ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Customer</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Amount</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Driver Reason</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Agent Type</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Time</th>
                </tr>
              </thead>
              <tbody style={{ color: '#cbd5e1' }}>
                {transactions.map(txn => {
                  const reason = txn.reason || {}
                  const driver = reason.primary_driver || reason.rule_name || 'baseline'
                  return (
                    <tr key={txn.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: '#818cf8' }}>
                        {txn.id.substring(0, 13)}...
                      </td>
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>{txn.customer_id}</td>
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 700, color: '#f8fafc' }}>
                        ₹{Number(txn.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <RiskBadge status={txn.status} score={txn.risk_score} />
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                        {driver}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', color: '#64748b' }}>{txn.agent_type || 'autonomous'}</td>
                      <td style={{ padding: '0.85rem 1rem', color: '#64748b', fontSize: '0.78rem' }}>
                        {new Date(txn.created_at || Date.now()).toLocaleTimeString()}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
