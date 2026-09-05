import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowRight, AlertCircle, Mail, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../lib/useAuth'

export default function SignUp() {
  const { session, merchantId, loading: authLoading, signUp } = useAuth()
  const navigate = useNavigate()

  // View state: 'form' | 'email_check'
  const [viewState, setViewState] = useState('form')

  // Form inputs
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // If already authenticated, redirect appropriately
  useEffect(() => {
    if (!authLoading && session) {
      if (merchantId) {
        navigate('/dashboard', { replace: true })
      } else {
        navigate('/organization-setup', { replace: true })
      }
    }
  }, [authLoading, session, merchantId, navigate])

  const handleSignUp = async (e) => {
    e.preventDefault()
    setError('')

    const trimmedEmail = email.trim()
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(trimmedEmail)) {
      setError('Please provide a valid work email address.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your password.')
      return
    }

    setLoading(true)

    try {
      const result = await signUp(trimmedEmail, password)
      if (!result.success) {
        setError(result.error || 'Failed to create account. Please try again.')
        setLoading(false)
        return
      }

      // CASE A — Email confirmation enabled
      if (result.needsEmailConfirmation) {
        setViewState('email_check')
      } else {
        // CASE B — Email confirmation disabled: session returned immediately
        navigate('/organization-setup')
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during signup.')
    } finally {
      setLoading(false)
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
      <div className="glass-card" style={{ width: '100%', maxWidth: '440px', padding: '2.5rem 2rem' }}>
        {/* Brand header */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
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
            {viewState === 'email_check' ? 'Check Your Email' : 'Create PayFilter Account'}
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            {viewState === 'email_check'
              ? 'Verification required to activate your account'
              : 'Join the AI-agent payment risk firewall platform'}
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

        {/* CASE A: Email confirmation state */}
        {viewState === 'email_check' ? (
          <div style={{ textAlign: 'center', padding: '0.5rem 0' }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.15)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
              color: '#818cf8'
            }}>
              <Mail size={30} />
            </div>

            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
              Check your email to verify your account.
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              We sent a verification link to <strong style={{ color: '#e2e8f0' }}>{email}</strong>. Please check your inbox and click the verification link before signing in.
            </p>

            <button
              onClick={() => navigate('/login')}
              style={{
                width: '100%',
                padding: '0.8rem',
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
                gap: '0.4rem',
                boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
              }}
            >
              Go to Sign In <ArrowRight size={15} />
            </button>
          </div>
        ) : (
          /* Normal 3-field registration form */
          <form onSubmit={handleSignUp} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Work Email
              </label>
              <input
                type="email"
                placeholder="founder@acme.com"
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
                Password (min. 8 characters)
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

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Confirm Password
              </label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
              disabled={loading}
              style={{
                marginTop: '0.5rem',
                padding: '0.75rem',
                borderRadius: '8px',
                background: loading ? '#475569' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.9rem',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
              }}
            >
              {loading ? 'Registering Account...' : 'Sign Up'}
              {!loading && <ArrowRight size={15} />}
            </button>

            <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.82rem', color: '#94a3b8' }}>
              Already registered?{' '}
              <Link to="/login" style={{ color: '#818cf8', fontWeight: 600, textDecoration: 'none' }}>
                Sign In
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
