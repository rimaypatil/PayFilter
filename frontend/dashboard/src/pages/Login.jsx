import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Lock, ArrowRight, AlertCircle } from 'lucide-react'
import { useAuth } from '../lib/useAuth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login, session, merchantId, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && session) {
      if (merchantId) {
        navigate('/dashboard', { replace: true })
      } else {
        navigate('/organization-setup', { replace: true })
      }
    }
  }, [loading, session, merchantId, navigate])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const result = await login(email, password)
      if (result.success) {
        if (result.hasMerchant) {
          navigate('/dashboard')
        } else {
          navigate('/organization-setup')
        }
      } else {
        setError(result.error || 'Invalid credentials provided. Please check your email and password.')
      }
    } catch (err) {
      setError(err.message || 'Invalid credentials provided. Please check your email and password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 50% 30%, rgba(99, 102, 241, 0.12) 0%, #070a12 70%)',
      padding: '1.5rem'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '2.5rem 2rem' }}>
        {/* Brand header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <img
            src="/payfilter-logo.png"
            alt="PayFilter"
            style={{
              height: '46px',
              width: 'auto',
              objectFit: 'contain',
              margin: '0 auto 1.25rem',
              display: 'block',
              background: 'transparent'
            }}
          />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.25rem' }}>
            Merchant Sign In
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Access your PayFilter risk monitor & confirmation console
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
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={15} /> {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
              Work Email
            </label>
            <input
              type="email"
              placeholder="analyst@acme.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.7rem 0.85rem',
                borderRadius: '8px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-subtle)',
                color: '#ffffff',
                fontSize: '0.88rem',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
              Password
            </label>
            <input
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.7rem 0.85rem',
                borderRadius: '8px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-subtle)',
                color: '#ffffff',
                fontSize: '0.88rem',
                outline: 'none'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              marginTop: '0.5rem',
              padding: '0.75rem',
              borderRadius: '8px',
              background: submitting ? '#475569' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.9rem',
              border: 'none',
              cursor: submitting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.4rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
            }}
          >
            {submitting ? 'Authenticating...' : 'Sign In to Dashboard'}
            {!submitting && <ArrowRight size={15} />}
          </button>

          <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '0.82rem', color: '#94a3b8' }}>
            New to PayFilter?{' '}
            <Link to="/signup" style={{ color: '#818cf8', fontWeight: 600, textDecoration: 'none' }}>
              Create an account
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
