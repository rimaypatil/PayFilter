import React, { useState, useEffect } from 'react'
import { Power, AlertOctagon, Key, ShieldAlert, CheckCircle2, Lock, AlertTriangle } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'
import RoleGate from '../components/RoleGate'

export default function KillSwitch() {
  const authContext = useAuth()
  const [isActive, setIsActive] = useState(false)
  const [stepUpCode, setStepUpCode] = useState('')
  const [reason, setReason] = useState('Suspected agent runaway / API compromise')
  const [devOtpIssued, setDevOtpIssued] = useState(null)
  const [loadingRequest, setLoadingRequest] = useState(false)
  const [loadingConfirm, setLoadingConfirm] = useState(false)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    async function checkCurrentStatus() {
      if (!authContext.merchantId) return
      try {
        const state = await api.getKillSwitchStatus(authContext)
        setIsActive(Boolean(state?.is_active))
      } catch (e) {
        console.error('Failed to get kill switch state:', e)
      }
    }
    if (!authContext.loading && authContext.merchantId) {
      checkCurrentStatus()
    }
  }, [authContext.merchantId, authContext.loading])

  const handleRequestStepUp = async () => {
    setLoadingRequest(true)
    setError('')
    setSuccessMsg('')
    try {
      const data = await api.requestKillSwitchOtp(authContext)
      setDevOtpIssued(data.code)
    } catch (err) {
      setError(err.message || 'Failed to request step-up code')
    } finally {
      setLoadingRequest(false)
    }
  }

  const handleConfirmToggle = async (targetActiveState) => {
    if (!stepUpCode.trim()) {
      setError('Please enter the 6-digit step-up verification code')
      return
    }

    setLoadingConfirm(true)
    setError('')
    try {
      const res = await api.confirmKillSwitch(authContext, stepUpCode, targetActiveState, reason)
      setIsActive(res.is_active)
      setDevOtpIssued(null)
      setStepUpCode('')
      setSuccessMsg(res.is_active
        ? 'EMERGENCY KILL SWITCH ACTIVATED. All incoming AI agent checkout transactions are now BLOCKED.'
        : 'Kill switch deactivated. Normal checkout evaluations resumed.'
      )
    } catch (err) {
      setError(err.detail || err.message || 'Failed to execute kill switch toggle')
    } finally {
      setLoadingConfirm(false)
    }
  }

  return (
    <RoleGate
      allow={['admin']}
      fallback={
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', maxWidth: '600px', margin: '3rem auto' }}>
          <AlertTriangle size={36} color="#fbbf24" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
            Admin Privileges Required
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Emergency kill switch controls can only be operated by users with the <strong>Admin</strong> role.
          </p>
        </div>
      }
    >
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <Power size={24} color={isActive ? '#f43f5e' : '#818cf8'} />
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
              Emergency Kill Switch
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Two-factor step-up protected emergency halt. Instantly stops all AI agent checkout evaluations.
          </p>
        </div>

        {/* STATUS BANNER */}
        <div style={{
          background: isActive ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.1)',
          border: `1px solid ${isActive ? 'rgba(244, 63, 94, 0.4)' : 'rgba(16, 185, 129, 0.25)'}`,
          borderRadius: '12px',
          padding: '1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          {isActive ? <AlertOctagon size={36} color="#f43f5e" /> : <CheckCircle2 size={36} color="#10b981" />}
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: isActive ? '#f87171' : '#34d399', marginBottom: '0.2rem' }}>
              CURRENT STATUS: {isActive ? 'ACTIVE (ALL PAYMENTS FROZEN)' : 'INACTIVE (NORMAL OPERATIONS)'}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
              {isActive
                ? 'Every pre-order check is immediately returning status="blocked" with reason="kill_switch_activated".'
                : 'Transactions are being evaluated normally against ML models and risk rules.'}
            </div>
          </div>
        </div>

        {successMsg && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            color: '#6ee7b7',
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <CheckCircle2 size={18} /> {successMsg}
          </div>
        )}

        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.4)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            color: '#fb7185',
            fontSize: '0.88rem'
          }}>
            {error}
          </div>
        )}

        {/* STEP-UP EXECUTION CARD */}
        <div className="glass-card" style={{ padding: '2rem', border: isActive ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid var(--border-subtle)' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
            {isActive ? 'Deactivate Kill Switch & Resume Operations' : 'Engage Emergency Kill Switch'}
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
            Requires <strong>Step-Up Two-Factor Authorization</strong>. Request a short-lived 6-digit one-time code to proceed.
          </p>

          {/* STEP 1: REQUEST OTP */}
          {!devOtpIssued ? (
            <div>
              <button
                onClick={handleRequestStepUp}
                disabled={loadingRequest}
                style={{
                  padding: '0.85rem 1.75rem',
                  borderRadius: '8px',
                  background: isActive ? '#334155' : 'linear-gradient(135deg, #f43f5e, #be123c)',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  border: 'none',
                  cursor: loadingRequest ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  boxShadow: isActive ? 'none' : '0 4px 15px rgba(244, 63, 94, 0.4)'
                }}
              >
                <Key size={16} />
                {loadingRequest ? 'Requesting Code...' : (isActive ? 'Request Step-Up Code to Resume' : 'Freeze All Agent Payments')}
              </button>
            </div>
          ) : (
            /* STEP 2: CONFIRM WITH OTP */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* DEV MODE OTP DISPLAY BANNER */}
              <div style={{
                background: 'rgba(99, 102, 241, 0.12)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '8px',
                padding: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ color: '#a5b4fc', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
                    [Dev Mode] Step-Up OTP Issued
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                    {devOtpIssued}
                  </div>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Expires in 5 minutes</span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
                  Enter 6-Digit Step-Up Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="e.g. 123456"
                  value={stepUpCode}
                  onChange={(e) => setStepUpCode(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '1.1rem',
                    fontFamily: 'var(--font-mono)',
                    letterSpacing: '0.2em',
                    outline: 'none'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>
                  Reason / Incident Log Entry
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  onClick={() => handleConfirmToggle(!isActive)}
                  disabled={loadingConfirm}
                  style={{
                    flex: 1,
                    padding: '0.85rem',
                    borderRadius: '8px',
                    background: !isActive ? 'linear-gradient(135deg, #f43f5e, #be123c)' : 'linear-gradient(135deg, #10b981, #059669)',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    border: 'none',
                    cursor: loadingConfirm ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    boxShadow: !isActive ? '0 4px 15px rgba(244, 63, 94, 0.4)' : '0 4px 15px rgba(16, 185, 129, 0.4)'
                  }}
                >
                  <Lock size={16} />
                  {loadingConfirm ? 'Verifying & Executing...' : (!isActive ? 'Confirm Emergency Halt' : 'Confirm Resume Payments')}
                </button>

                <button
                  onClick={() => { setDevOtpIssued(null); setStepUpCode(''); }}
                  style={{
                    padding: '0.85rem 1.25rem',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid var(--border-subtle)',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    fontWeight: 600,
                    fontSize: '0.85rem'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </RoleGate>
  )
}
