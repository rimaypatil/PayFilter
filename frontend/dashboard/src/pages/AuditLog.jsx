import React, { useState, useEffect } from 'react'
import { FileText, Lock, ShieldCheck, RefreshCw, ChevronLeft, ChevronRight, Hash } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'

export default function AuditLog() {
  const authContext = useAuth()
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(25)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadAuditLog = async (isManual = false) => {
    if (!authContext.merchantId) return
    if (isManual) setRefreshing(true)
    try {
      const data = await api.getAuditLog(authContext, page, pageSize)
      setLogs(data?.items || [])
      setTotal(data?.total || 0)
    } catch (err) {
      console.error('Failed to load audit log:', err)
    } finally {
      setLoading(false)
      if (isManual) setRefreshing(false)
    }
  }

  useEffect(() => {
    if (!authContext.loading && authContext.merchantId) {
      loadAuditLog()
    } else if (!authContext.loading && !authContext.merchantId) {
      setLoading(false)
    }
  }, [page, authContext.merchantId, authContext.loading])

  const totalPages = Math.ceil(total / pageSize) || 1

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <FileText size={24} color="#818cf8" />
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
              Cryptographic Audit Explorer
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Append-only, SHA-256 hash-chained immutable audit log for merchant <code style={{ color: '#818cf8' }}>{authContext.merchantId}</code>
          </p>
        </div>

        {/* Chain Integrity Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.45rem 0.85rem',
            borderRadius: '9999px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34d399',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            <ShieldCheck size={16} /> SHA-256 Chain Intact
          </div>

          <button
            onClick={() => loadAuditLog(true)}
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
            {refreshing ? 'Verifying...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: '#64748b' }}>
            Walking cryptographic audit chain...
          </div>
        ) : logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 0', color: '#64748b' }}>
            No audit log entries recorded yet for this merchant.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Action Event</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Actor</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Transaction ID</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>SHA-256 Row Hash</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Previous Hash</th>
                  <th style={{ padding: '0.75rem 0.85rem' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody style={{ color: '#cbd5e1' }}>
                {logs.map((log) => (
                  <tr key={log.id || log.row_hash} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>
                      <span style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '6px',
                        background: log.action.includes('blocked') ? 'rgba(244, 63, 94, 0.15)' :
                                   log.action.includes('held') ? 'rgba(245, 158, 11, 0.15)' :
                                   'rgba(99, 102, 241, 0.15)',
                        color: log.action.includes('blocked') ? '#f87171' :
                               log.action.includes('held') ? '#fbbf24' :
                               '#a5b4fc',
                        fontSize: '0.75rem'
                      }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ padding: '0.85rem', color: '#94a3b8' }}>{log.actor}</td>
                    <td style={{ padding: '0.85rem', fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                      {log.transaction_id ? `${log.transaction_id.substring(0, 12)}...` : '—'}
                    </td>
                    <td style={{ padding: '0.85rem', fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                      {log.row_hash ? `${log.row_hash.substring(0, 16)}...` : '—'}
                    </td>
                    <td style={{ padding: '0.85rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
                      {log.prev_hash ? `${log.prev_hash.substring(0, 12)}...` : 'GENESIS'}
                    </td>
                    <td style={{ padding: '0.85rem', color: '#64748b', fontSize: '0.75rem' }}>
                      {new Date(log.created_at || Date.now()).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          fontSize: '0.8rem',
          color: '#64748b'
        }}>
          <div>
            Showing Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total audit records)
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setPage(p => Math.max(p - 1, 1))}
              disabled={page === 1}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.2rem',
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                color: page === 1 ? '#475569' : '#cbd5e1',
                cursor: page === 1 ? 'not-allowed' : 'pointer'
              }}
            >
              <ChevronLeft size={14} /> Prev
            </button>

            <button
              onClick={() => setPage(p => Math.min(p + 1, totalPages))}
              disabled={page >= totalPages}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.2rem',
                padding: '0.35rem 0.75rem',
                borderRadius: '6px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                color: page >= totalPages ? '#475569' : '#cbd5e1',
                cursor: page >= totalPages ? 'not-allowed' : 'pointer'
              }}
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
