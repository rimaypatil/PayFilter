import React, { useState } from 'react'
import { Key, Copy, Check, AlertTriangle, ArrowRight, ShieldCheck, CheckCircle2, Lock } from 'lucide-react'

export default function SignUp() {
  const [merchantName, setMerchantName] = useState('')
  const [adminUserId, setAdminUserId] = useState(`usr_${Math.random().toString(36).substring(2, 11)}`)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [signupResult, setSignupResult] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!merchantName.trim()) {
      setError('Merchant / Business Name is required')
      return
    }

    setLoading(true)
    setError('')

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
      const res = await fetch(`${backendUrl}/merchants/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: merchantName.trim(),
          admin_user_id: adminUserId.trim(),
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Failed to register merchant account')
      }

      const data = await res.json()
      setSignupResult(data)
    } catch (err) {
      setError(err.message || 'Network error connecting to backend API')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (signupResult?.api_key) {
      navigator.clipboard.writeText(signupResult.api_key)
      setCopied(true)
      setTimeout(() => setCopied(false), 3000)
    }
  }

  return (
    <div style={{ maxWidth: '640px', margin: '4rem auto 6rem', padding: '0 1.5rem' }}>
      {!signupResult ? (
        <div className="glass-panel" style={{ padding: '2.5rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
              boxShadow: '0 0 25px rgba(99, 102, 241, 0.4)'
            }}>
              <Key size={24} color="#ffffff" />
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem' }}>
              Create Merchant Account
            </h1>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
              Register your merchant organization and receive your live PayFilter API key.
            </p>
          </div>

          {error && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#fb7185',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.85rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertTriangle size={16} /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.5rem' }}>
                Business / Organization Name
              </label>
              <input
                type="text"
                placeholder="e.g. Acme Global Commerce"
                value={merchantName}
                onChange={(e) => setMerchantName(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#ffffff',
                  fontSize: '0.9rem',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.5rem' }}>
                Admin User Identifier (Supabase Auth UID)
              </label>
              <input
                type="text"
                value={adminUserId}
                onChange={(e) => setAdminUserId(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#94a3b8',
                  fontSize: '0.9rem',
                  outline: 'none',
                  fontFamily: 'var(--font-mono)'
                }}
              />
              <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.35rem', display: 'block' }}>
                This user ID will be granted initial 'admin' role privileges for your merchant.
              </span>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '1rem',
                padding: '0.85rem',
                borderRadius: '8px',
                background: loading ? '#475569' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.95rem',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
              }}
            >
              {loading ? 'Registering Organization...' : 'Generate API Key & Register'}
              {!loading && <ArrowRight size={16} />}
            </button>
          </form>
        </div>
      ) : (
        /* SINGLE REVEAL KEY DISPLAY */
        <div className="glass-panel" style={{ padding: '2.5rem', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
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
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399', marginBottom: '0.25rem' }}>
              Merchant Successfully Registered!
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Organization: <strong>{signupResult.name}</strong> ({signupResult.merchant_id})
            </p>
          </div>

          {/* CRITICAL WARNING BANNER */}
          <div style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            display: 'flex',
            gap: '0.75rem'
          }}>
            <AlertTriangle size={22} color="#fbbf24" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ color: '#fde68a', fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.25rem' }}>
                Save this API Key immediately
              </div>
              <div style={{ color: '#fbbf24', fontSize: '0.8rem', lineHeight: 1.5 }}>
                For security reasons, this plaintext key is shown <strong>only once</strong> and cannot be recovered.
                Only the SHA-256 hash is stored in PayFilter.
              </div>
            </div>
          </div>

          {/* Key Display Box */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>
                Live Merchant API Key
              </span>
              <button
                onClick={handleCopy}
                style={{
                  background: copied ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: '6px',
                  padding: '0.3rem 0.65rem',
                  color: copied ? '#34d399' : '#cbd5e1',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem'
                }}
              >
                {copied ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
                {copied ? 'Copied!' : 'Copy Key'}
              </button>
            </div>
            <code style={{
              display: 'block',
              fontSize: '0.9rem',
              color: '#a7f3d0',
              wordBreak: 'break-all',
              fontFamily: 'var(--font-mono)'
            }}>
              {signupResult.api_key}
            </code>
          </div>

          {/* Next Steps CTA */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <a
              href="http://localhost:3001"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                width: '100%',
                padding: '0.85rem',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.95rem',
                textAlign: 'center',
                textDecoration: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 15px rgba(16, 185, 129, 0.35)'
              }}
            >
              Log in to Merchant Dashboard <ArrowRight size={16} />
            </a>

            <button
              onClick={() => setSignupResult(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                fontSize: '0.85rem',
                cursor: 'pointer',
                padding: '0.5rem'
              }}
            >
              Register another merchant
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
