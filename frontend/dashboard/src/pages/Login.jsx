import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Lock, ArrowRight, AlertCircle } from 'lucide-react'
import { useAuth } from '../lib/useAuth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const result = await login(email, password)
      if (result.success) {
        navigate('/')
      } else {
        setError('Invalid credentials provided. Please check your email and password.')
      }
    } catch (err) {
      setError('Invalid credentials provided. Please check your email and password.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleQuickLogin = (roleType) => {
    const mockEmail = roleType === 'admin' ? 'admin@merchant.com' : 'analyst@merchant.com'
    login(mockEmail, 'password123', roleType)
    navigate('/')
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
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            <Shield size={22} color="#ffffff" />
          </div>
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

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
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
        </form>

        {/* Demo Fast-Login Helpers */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem', textAlign: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', marginBottom: '0.75rem' }}>
            Demo / Evaluation Quick Access
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => handleQuickLogin('admin')}
              style={{
                flex: 1,
                padding: '0.5rem',
                borderRadius: '6px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                color: '#a5b4fc',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Sign In as Admin
            </button>

            <button
              onClick={() => handleQuickLogin('analyst')}
              style={{
                flex: 1,
                padding: '0.5rem',
                borderRadius: '6px',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                color: '#6ee7b7',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Sign In as Analyst
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
