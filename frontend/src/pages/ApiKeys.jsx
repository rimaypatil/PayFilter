import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Key,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  ExternalLink,
  Lock,
  Server,
  ArrowRight,
  Code,
  Terminal,
  Zap
} from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'

export default function ApiKeys() {
  const authContext = useAuth()
  const { role, merchantId } = authContext

  // API Key Status state
  const [statusLoading, setStatusLoading] = useState(true)
  const [merchantName, setMerchantName] = useState('Merchant Organization')
  const [isActive, setIsActive] = useState(true)
  const [maskedKey, setMaskedKey] = useState('pf_live_••••••••••••••••')
  const [lastRotated, setLastRotated] = useState(null)
  const [endpointPath, setEndpointPath] = useState('/transactions/check')

  // Rotation confirmation modal state
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [rotating, setRotating] = useState(false)

  // Ephemeral single-reveal plaintext key state (NEVER persisted to storage or logged)
  const [newPlaintextKey, setNewPlaintextKey] = useState(null)

  // Confirmed role from backend authority
  const [serverRole, setServerRole] = useState(role || null)

  const effectiveRole = serverRole || role

  // Copy feedback states
  const [copiedNewKey, setCopiedNewKey] = useState(false)
  const [copiedEndpoint, setCopiedEndpoint] = useState(false)
  const [copiedCurl, setCopiedCurl] = useState(false)

  // Feedback & error alerts
  const [errorMsg, setErrorMsg] = useState('')
  const [successNotice, setSuccessNotice] = useState('')

  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
  const fullEndpointUrl = `${backendBaseUrl}${endpointPath}`

  // Security: Clean up any ephemeral secret key from memory if the component unmounts
  useEffect(() => {
    return () => {
      setNewPlaintextKey(null)
    }
  }, [])

  // Fetch initial API key metadata
  const loadKeyStatus = async () => {
    setStatusLoading(true)
    setErrorMsg('')
    try {
      const data = await api.getApiKeyStatus(authContext)
      if (data) {
        setMerchantName(data.merchant_name || 'Merchant Organization')
        setIsActive(Boolean(data.is_active))
        setMaskedKey(data.masked_key || 'pf_live_••••••••••••••••')
        setLastRotated(data.created_at || null)
        if (data.role) {
          setServerRole(data.role)
          if (authContext.setRole && authContext.role !== data.role) {
            authContext.setRole(data.role)
          }
        }
        if (data.merchant_id && authContext.setMerchantId && authContext.merchantId !== data.merchant_id) {
          authContext.setMerchantId(data.merchant_id)
        }
        if (data.transaction_endpoint) {
          setEndpointPath(data.transaction_endpoint)
        }
      }
    } catch (err) {
      handleApiError(err, 'Failed to fetch API key metadata')
    } finally {
      setStatusLoading(false)
    }
  }

  useEffect(() => {
    if (!authContext.loading && merchantId) {
      loadKeyStatus()
    } else if (!authContext.loading && !merchantId) {
      setStatusLoading(false)
    }
  }, [merchantId, authContext.loading])

  // Safe user-facing error handler (never reveals stack traces or sensitive internals)
  const handleApiError = (err, fallbackText) => {
    const status = err.status || (err.response && err.response.status)
    if (status === 401) {
      setErrorMsg('Your session has expired. Please sign in again.')
    } else if (status === 403) {
      setErrorMsg('Access Denied (403 Forbidden): Only users with the Admin role are authorized to rotate merchant API keys.')
    } else if (status === 404) {
      setErrorMsg('Merchant account record not found. Please refresh the page.')
    } else if (status === 409) {
      setErrorMsg('A conflict occurred during key rotation. Please try again in a few moments.')
    } else if (status === 500) {
      setErrorMsg('PayFilter server encountered an unexpected error. Please contact security support.')
    } else if (err.message && err.message.toLowerCase().includes('failed to fetch')) {
      setErrorMsg('Network error: Unable to communicate with PayFilter security backend. Please verify your connection.')
    } else {
      setErrorMsg(err.detail || err.message || fallbackText)
    }
  }

  // Handle Rotation Initiation
  const handleOpenRotateModal = () => {
    setErrorMsg('')
    setSuccessNotice('')
    if (effectiveRole !== 'admin') {
      setErrorMsg('Access Denied: Only users with the Admin role can rotate API keys. Analysts have read-only privileges.')
      return
    }
    setShowConfirmModal(true)
  }

  // Execute rotation against backend
  const handleConfirmRotation = async () => {
    setRotating(true)
    setErrorMsg('')
    try {
      const response = await api.rotateApiKey(authContext)
      // Ephemeral storage only in React state — NEVER saved to localStorage or sessionStorage
      if (response && response.api_key) {
        setNewPlaintextKey(response.api_key)
        setShowConfirmModal(false)
        setSuccessNotice('New API key generated successfully. Save it immediately!')
        // Refresh masked timestamp
        setLastRotated(new Date().toISOString())
      } else {
        throw new Error('No API key returned from server')
      }
    } catch (err) {
      handleApiError(err, 'Failed to rotate API key')
      setShowConfirmModal(false)
    } finally {
      setRotating(false)
    }
  }

  // Dismiss single-reveal modal and permanently wipe plaintext key from React state
  const handleDismissNewKey = () => {
    setNewPlaintextKey(null)
    setCopiedNewKey(false)
    setSuccessNotice('Active API key is now secured and masked.')
  }

  const handleCopyNewKey = async () => {
    if (!newPlaintextKey) return
    try {
      await navigator.clipboard.writeText(newPlaintextKey)
      setCopiedNewKey(true)
      setTimeout(() => setCopiedNewKey(false), 3000)
    } catch (e) {
      // fallback
    }
  }

  const handleCopyEndpoint = async () => {
    try {
      await navigator.clipboard.writeText(fullEndpointUrl)
      setCopiedEndpoint(true)
      setTimeout(() => setCopiedEndpoint(false), 2500)
    } catch (e) {
      // fallback
    }
  }

  const curlSample = `curl -X POST ${fullEndpointUrl} \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: pf_live_••••••••••••••••" \\
  -d '{
    "transaction_id": "txn_${Date.now().toString().slice(-6)}",
    "amount": 12500.00,
    "customer_id": "cust_ai_042",
    "agent_type": "autonomous_buyer"
  }'`

  const handleCopyCurl = async () => {
    try {
      await navigator.clipboard.writeText(curlSample)
      setCopiedCurl(true)
      setTimeout(() => setCopiedCurl(false), 2500)
    } catch (e) {
      // fallback
    }
  }

  if (authContext.loading) {
    return (
      <div style={{ padding: '4rem 2rem', textAlign: 'center', color: '#94a3b8' }}>
        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem', display: 'block', color: '#818cf8' }} />
        <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>Loading API key management context...</span>
      </div>
    )
  }

  if (authContext.role === 'unassigned' || !merchantId) {
    return (
      <div className="glass-card" style={{ maxWidth: '620px', margin: '4rem auto', padding: '2.5rem', textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.75rem' }}>
          No Merchant Organization Assigned
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.75rem' }}>
          API key management requires an active merchant organization membership. Please register or join an organization to generate and rotate API keys.
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

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2))',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '10px',
              padding: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8'
            }}>
              <Key size={22} />
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
              API Keys & Developer Access
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0, maxWidth: '650px' }}>
            Manage merchant credentials for authenticating your AI agent bridge with the PayFilter real-time risk engine.
          </p>
        </div>

        {/* Merchant Identity Card */}
        <div className="glass-card" style={{
          padding: '0.75rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          border: '1px solid rgba(255,255,255,0.08)'
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>
              Merchant Tenant
            </div>
            <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#ffffff' }}>
              {merchantName}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
              ID: {merchantId?.slice(0, 18)}...
            </div>
          </div>
          <div style={{
            padding: '0.35rem 0.65rem',
            borderRadius: '9999px',
            fontSize: '0.72rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            background: effectiveRole === 'admin' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            color: effectiveRole === 'admin' ? '#a5b4fc' : '#6ee7b7',
            border: `1px solid ${effectiveRole === 'admin' ? 'rgba(99, 102, 241, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
          }}>
            {(effectiveRole || 'ANALYST').toUpperCase()}
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div style={{
          background: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          color: '#fb7185',
          fontSize: '0.88rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          boxShadow: '0 4px 15px rgba(244, 63, 94, 0.15)'
        }}>
          <ShieldAlert size={20} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}>{errorMsg}</div>
          <button
            onClick={() => setErrorMsg('')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fb7185',
              cursor: 'pointer',
              fontWeight: 700
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Success Alert */}
      {successNotice && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          color: '#34d399',
          fontSize: '0.88rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          boxShadow: '0 4px 15px rgba(16, 185, 129, 0.15)'
        }}>
          <CheckCircle2 size={20} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1 }}>{successNotice}</div>
          <button
            onClick={() => setSuccessNotice('')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#34d399',
              cursor: 'pointer',
              fontWeight: 700
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* SINGLE-REVEAL NEW KEY MODAL / BANNER (Revealed exactly ONCE) */}
      {newPlaintextKey && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.95), rgba(15, 23, 42, 0.98))',
          border: '2px solid #818cf8',
          borderRadius: '14px',
          padding: '2rem',
          boxShadow: '0 0 35px rgba(99, 102, 241, 0.35)',
          position: 'relative',
          animation: 'fadeIn 0.2s ease-in-out'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
            <span style={{
              background: '#4f46e5',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              letterSpacing: '0.05em'
            }}>
              NEW API KEY GENERATED
            </span>
            <span style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>
              Single-Reveal Security Mode
            </span>
          </div>

          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
            Your New Merchant API Key
          </h3>

          <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginBottom: '1.25rem' }}>
            Copy and securely store this key now. For your security, this key is SHA-256 hashed on the server and{' '}
            <strong style={{ color: '#fb7185' }}>will NEVER be displayed again</strong>.
          </p>

          {/* Plaintext Key Box */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            marginBottom: '1.25rem'
          }}>
            <code style={{
              color: '#a5f3fc',
              fontSize: '1.05rem',
              fontWeight: 700,
              wordBreak: 'break-all',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.04em'
            }}>
              {newPlaintextKey}
            </code>

            <button
              onClick={handleCopyNewKey}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.65rem 1.1rem',
                borderRadius: '8px',
                background: copiedNewKey ? '#059669' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                color: '#ffffff',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                flexShrink: 0
              }}
            >
              {copiedNewKey ? (
                <>
                  <Check size={16} /> Copied!
                </>
              ) : (
                <>
                  <Copy size={16} /> Copy API Key
                </>
              )}
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b', fontSize: '0.82rem' }}>
              <AlertTriangle size={16} />
              Save this key now. For security reasons it will not be displayed again.
            </div>

            <button
              onClick={handleDismissNewKey}
              style={{
                padding: '0.65rem 1.5rem',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}
            >
              I Have Securely Saved This Key
            </button>
          </div>
        </div>
      )}

      {/* 1. API KEY OVERVIEW CARD */}
      <div className="glass-card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              PAYFILTER API KEY
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                fontSize: '0.78rem',
                fontWeight: 800,
                letterSpacing: '0.05em',
                background: isActive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                color: isActive ? '#34d399' : '#f87171',
                border: `1px solid ${isActive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
              }}>
                <span style={{
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  background: isActive ? '#10b981' : '#f43f5e',
                  boxShadow: isActive ? '0 0 8px #10b981' : 'none'
                }} />
                {isActive ? 'ACTIVE' : 'INACTIVE'}
              </div>

              {lastRotated && (
                <span style={{ color: '#64748b', fontSize: '0.8rem' }}>
                  Updated: {new Date(lastRotated).toLocaleDateString()} {new Date(lastRotated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>
          </div>

          {/* Action Button: ROTATE API KEY */}
          <div>
            <button
              onClick={handleOpenRotateModal}
              disabled={rotating || effectiveRole !== 'admin'}
              style={{
                padding: '0.75rem 1.4rem',
                borderRadius: '8px',
                background: effectiveRole === 'admin'
                  ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)'
                  : 'rgba(255, 255, 255, 0.05)',
                color: effectiveRole === 'admin' ? '#ffffff' : '#64748b',
                border: effectiveRole === 'admin' ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255, 255, 255, 0.1)',
                fontWeight: 700,
                fontSize: '0.88rem',
                cursor: effectiveRole === 'admin' ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: effectiveRole === 'admin' ? '0 4px 18px rgba(99, 102, 241, 0.3)' : 'none',
                transition: 'all 0.2s'
              }}
              title={effectiveRole !== 'admin' ? 'Admin role required to rotate API keys' : 'Rotate API Key'}
            >
              <RefreshCw size={16} className={rotating ? 'spin' : ''} />
              ROTATE API KEY
            </button>
            {effectiveRole !== 'admin' && (
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.35rem', textAlign: 'right' }}>
                <Lock size={12} style={{ display: 'inline', marginRight: '3px' }} />
                Admin role required
              </div>
            )}
          </div>
        </div>

        {/* Masked Key Display Box */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.45)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px',
          padding: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
              Active Key Secret (SHA-256 Hashed in Vault)
            </div>
            <div style={{
              fontSize: '1.2rem',
              fontWeight: 700,
              fontFamily: 'var(--font-mono)',
              color: '#e2e8f0',
              letterSpacing: '0.15em'
            }}>
              {maskedKey}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.78rem', color: '#94a3b8' }}>
            <span style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '0.3rem 0.6rem',
              borderRadius: '6px',
              border: '1px solid rgba(255,255,255,0.06)'
            }}>
              Auth Scheme: X-API-Key
            </span>
            <span style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '0.3rem 0.6rem',
              borderRadius: '6px',
              border: '1px solid rgba(255,255,255,0.06)'
            }}>
              Algorithm: SHA-256
            </span>
          </div>
        </div>
      </div>

      {/* ROTATION CONFIRMATION MODAL */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1.5rem'
        }}>
          <div className="glass-card" style={{
            maxWidth: '520px',
            width: '100%',
            padding: '2rem',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            background: 'var(--bg-surface)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: '#fb7185' }}>
              <div style={{
                background: 'rgba(244, 63, 94, 0.15)',
                padding: '0.6rem',
                borderRadius: '10px',
                display: 'flex'
              }}>
                <AlertTriangle size={24} />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                Confirm API Key Rotation
              </h3>
            </div>

            <p style={{ color: '#cbd5e1', fontSize: '0.92rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
              Rotating this key will <strong>immediately invalidate the current API key</strong>. Any AI agents using the old key will stop working until updated with the newly generated key.
            </p>

            <div style={{
              background: 'rgba(244, 63, 94, 0.08)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              borderRadius: '8px',
              padding: '0.85rem',
              fontSize: '0.8rem',
              color: '#fda4af',
              marginBottom: '1.75rem'
            }}>
              <strong>Notice:</strong> This operation creates a new cryptographic key on the backend and updates the merchant vault. The old key will immediately return <code>401 Unauthorized</code>.
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={rotating}
                style={{
                  padding: '0.65rem 1.25rem',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#e2e8f0',
                  fontWeight: 600,
                  fontSize: '0.88rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>

              <button
                onClick={handleConfirmRotation}
                disabled={rotating}
                style={{
                  padding: '0.65rem 1.4rem',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #e11d48, #be123c)',
                  border: 'none',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.88rem',
                  cursor: rotating ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 4px 15px rgba(225, 29, 72, 0.4)'
                }}
              >
                {rotating ? (
                  <>
                    <RefreshCw size={15} className="spin" />
                    Rotating Key...
                  </>
                ) : (
                  'Rotate Key'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. DEVELOPER INTEGRATION SECTION */}
      <div className="glass-card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#818cf8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
            DEVELOPER INTEGRATION INFORMATION
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
            PayFilter Transaction Verification Endpoint
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginTop: '0.25rem', margin: 0 }}>
            Configure your AI Agent bridge or backend checkout service to evaluate orders before submitting to payment gateway.
          </p>
        </div>

        {/* Endpoint Bar */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.5)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{
              background: '#047857',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '0.25rem 0.65rem',
              borderRadius: '6px',
              letterSpacing: '0.05em'
            }}>
              POST
            </span>
            <code style={{
              color: '#38bdf8',
              fontSize: '0.95rem',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)'
            }}>
              {fullEndpointUrl}
            </code>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              onClick={handleCopyEndpoint}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.9rem',
                borderRadius: '6px',
                background: copiedEndpoint ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                border: copiedEndpoint ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.15)',
                color: copiedEndpoint ? '#34d399' : '#e2e8f0',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {copiedEndpoint ? <Check size={14} /> : <Copy size={14} />}
              {copiedEndpoint ? 'Endpoint Copied' : 'Copy Endpoint'}
            </button>

            <Link
              to="/docs"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.9rem',
                borderRadius: '6px',
                background: 'rgba(99, 102, 241, 0.15)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#a5b4fc',
                fontSize: '0.8rem',
                fontWeight: 600,
                textDecoration: 'none',
                transition: 'all 0.15s'
              }}
            >
              <ExternalLink size={14} />
              View API Documentation
            </Link>
          </div>
        </div>

        {/* Authentication Header Note */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.85rem 1.1rem',
          background: 'rgba(99, 102, 241, 0.07)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#cbd5e1'
        }}>
          <Server size={18} color="#818cf8" style={{ flexShrink: 0 }} />
          <div>
            <strong>Required Header:</strong> Authenticate every request by attaching{' '}
            <code style={{ background: 'rgba(0,0,0,0.4)', padding: '0.15rem 0.4rem', borderRadius: '4px', color: '#f8fafc' }}>
              X-API-Key: &lt;merchant API key&gt;
            </code>
          </div>
        </div>

        {/* Interactive cURL Preview */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sample Request (cURL)
            </span>
            <button
              onClick={handleCopyCurl}
              style={{
                background: 'transparent',
                border: 'none',
                color: copiedCurl ? '#34d399' : '#818cf8',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              {copiedCurl ? <Check size={13} /> : <Copy size={13} />}
              {copiedCurl ? 'cURL Copied' : 'Copy cURL'}
            </button>
          </div>

          <pre style={{
            background: 'rgba(0, 0, 0, 0.65)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '1rem',
            color: '#e2e8f0',
            fontSize: '0.82rem',
            overflowX: 'auto',
            fontFamily: 'var(--font-mono)',
            margin: 0,
            lineHeight: 1.5
          }}>
            {curlSample}
          </pre>
        </div>
      </div>

      {/* 3. DEVELOPER WORKFLOW ARCHITECTURE VISUALIZER */}
      <div className="glass-card" style={{ padding: '2rem' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
            INTEGRATION LIFECYCLE
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
            Autonomous AI Agent Execution Pipeline
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginTop: '0.25rem', margin: 0 }}>
            How merchant AI agents securely clear pre-order risk evaluations through PayFilter before executing transactions.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          position: 'relative'
        }}>
          {/* Step 1 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#818cf8', letterSpacing: '0.05em' }}>
                STEP 01
              </span>
              <Key size={16} color="#818cf8" />
            </div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
              Generate API Key
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Admin generates and saves merchant key securely.
            </div>
          </div>

          {/* Step 2 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#a855f7', letterSpacing: '0.05em' }}>
                STEP 02
              </span>
              <Lock size={16} color="#a855f7" />
            </div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
              Configure AI Bridge
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Supply key to server-side AI Agent environment via <code>X-API-Key</code>.
            </div>
          </div>

          {/* Step 3 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.05em' }}>
                STEP 03
              </span>
              <Terminal size={16} color="#38bdf8" />
            </div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
              Call /transactions/check
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Agent submits pre-order payload before payment commitment.
            </div>
          </div>

          {/* Step 4 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#f59e0b', letterSpacing: '0.05em' }}>
                STEP 04
              </span>
              <Zap size={16} color="#f59e0b" />
            </div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
              PayFilter Evaluates
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Risk engine checks velocity, caps, kill switch, and ML heuristics.
            </div>
          </div>

          {/* Step 5 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.65rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#10b981', letterSpacing: '0.05em' }}>
                STEP 05
              </span>
              <CheckCircle2 size={16} color="#10b981" />
            </div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
              Gateway Execution
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.5 }}>
              APPROVED order initiates Razorpay; HELD queues for operator review.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
