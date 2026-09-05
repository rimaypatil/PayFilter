import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building, ArrowRight, ShieldCheck, Key, Copy, Check, AlertCircle } from 'lucide-react'
import { useAuth } from '../lib/useAuth'

export default function OrganizationSetup() {
  const { session, user, setMerchantId, setRole, setMerchantName, refreshProfile } = useAuth()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [createdData, setCreatedData] = useState(null)
  const [copiedKey, setCopiedKey] = useState(false)

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

  const handleCreateOrganization = async (e) => {
    e.preventDefault()
    setError('')
    const trimmed = name.trim()
    if (trimmed.length < 2) {
      setError('Organization name must be at least 2 characters.')
      return
    }

    const token = session?.access_token
    if (!token) {
      setError('Authenticated session is missing. Please sign in again.')
      navigate('/login')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${BACKEND_URL}/merchants/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: trimmed
        })
      })

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        throw new Error(errBody.detail || `Setup failed with status ${res.status}`)
      }

      const data = await res.json()
      setCreatedData(data)
    } catch (err) {
      setError(err.message || 'Failed to create merchant organization.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopyApiKey = async () => {
    if (!createdData?.api_key) return
    try {
      await navigator.clipboard.writeText(createdData.api_key)
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2500)
    } catch (e) {
      // fallback
    }
  }

  const handleProceedToDashboard = async () => {
    if (createdData) {
      if (setMerchantId) setMerchantId(createdData.merchant_id)
      if (setRole) setRole('admin')
      if (setMerchantName) setMerchantName(createdData.name)
      if (refreshProfile) await refreshProfile()
    }
    navigate('/dashboard', { replace: true })
  }

  // STEP 2: Organization Created Successfully -> Single-reveal API Key
  if (createdData) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle at 50% 30%, rgba(99, 102, 241, 0.15) 0%, #070a12 70%)',
        padding: '1.5rem'
      }}>
        <div className="glass-card" style={{ width: '100%', maxWidth: '540px', padding: '2.5rem 2rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
              color: '#34d399'
            }}>
              <ShieldCheck size={28} />
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.4rem' }}>
              Organization Ready
            </h1>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', margin: 0 }}>
              <strong style={{ color: '#f8fafc' }}>{createdData.name}</strong> is now registered on PayFilter with you as <span style={{ color: '#818cf8', fontWeight: 700 }}>ADMIN</span>.
            </p>
          </div>

          {/* Primary API Key Display */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.6)',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            borderRadius: '10px',
            padding: '1.25rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#818cf8', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em' }}>
                <Key size={14} /> PRIMARY API KEY
              </div>
              <span style={{ fontSize: '0.72rem', color: '#f59e0b' }}>
                Single Reveal Mode
              </span>
            </div>

            <p style={{ color: '#94a3b8', fontSize: '0.78rem', marginBottom: '0.75rem', lineHeight: 1.5 }}>
              Copy your merchant API key now to connect your AI agent bridge. For security, this plaintext key is not stored in the database.
            </p>

            <div style={{
              background: 'rgba(0, 0, 0, 0.8)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.75rem'
            }}>
              <code style={{ color: '#38bdf8', fontSize: '0.92rem', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
                {createdData.api_key}
              </code>
              <button
                onClick={handleCopyApiKey}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.5rem 0.85rem',
                  borderRadius: '6px',
                  background: copiedKey ? '#059669' : 'rgba(99, 102, 241, 0.2)',
                  border: copiedKey ? '1px solid #10b981' : '1px solid rgba(99, 102, 241, 0.4)',
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  flexShrink: 0
                }}
              >
                {copiedKey ? <Check size={14} /> : <Copy size={14} />}
                {copiedKey ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>

          <button
            onClick={handleProceedToDashboard}
            style={{
              width: '100%',
              padding: '0.85rem',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.92rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 18px rgba(99, 102, 241, 0.35)'
            }}
          >
            Enter PayFilter Dashboard <ArrowRight size={16} />
          </button>
        </div>
      </div>
    )
  }

  // STEP 1: Organization Creation Form
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 50% 30%, rgba(99, 102, 241, 0.12) 0%, #070a12 70%)',
      padding: '1.5rem'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '440px', padding: '2.5rem 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <img
            src="/payfilter-logo.png"
            alt="PayFilter"
            style={{
              height: '42px',
              width: 'auto',
              objectFit: 'contain',
              margin: '0 auto 1.25rem',
              display: 'block'
            }}
          />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.35rem' }}>
            Set Up Your Organization
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Signed in as <strong style={{ color: '#cbd5e1' }}>{user?.email}</strong>. Create your merchant tenant to initialize real-time payment firewall rules.
          </p>
        </div>

        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '8px',
            padding: '0.75rem',
            marginBottom: '1.25rem',
            color: '#fb7185',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} /> {error}
          </div>
        )}

        <form onSubmit={handleCreateOrganization} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
              Merchant / Organization Name
            </label>
            <div style={{ position: 'relative' }}>
              <Building size={16} color="#64748b" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="e.g. Acme Electronics, Nova Retail"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem 0.85rem 0.75rem 2.4rem',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border-subtle)',
                  color: '#ffffff',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
            </div>
            <span style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.35rem', display: 'block' }}>
              This defines your isolated merchant tenant and default risk policy limits.
            </span>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '0.8rem',
              borderRadius: '8px',
              background: loading ? '#475569' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.92rem',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.45rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
            }}
          >
            {loading ? 'Creating Organization...' : 'Create Organization & Continue'}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>
      </div>
    </div>
  )
}
