import React, { useEffect } from 'react'
import { ArrowRight, ShieldCheck } from 'lucide-react'

export default function SignUp() {
  useEffect(() => {
    // Redirect to the centralized authentication & merchant onboarding portal
    window.location.href = 'http://localhost:3001/signup'
  }, [])

  return (
    <div style={{ maxWidth: '520px', margin: '6rem auto', padding: '0 1.5rem', textAlign: 'center' }}>
      <div className="glass-panel" style={{ padding: '3rem 2rem' }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'rgba(124, 58, 237, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.5rem'
        }}>
          <ShieldCheck size={32} color="#a855f7" />
        </div>

        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginBottom: '0.5rem' }}>
          Opening Merchant Registration
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '2rem', lineHeight: 1.5 }}>
          Redirecting to the PayFilter secure account creation and organization provisioning portal...
        </p>

        <a
          href="http://localhost:3001/signup"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            borderRadius: '9999px',
            background: 'linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #c084fc 100%)',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '0.9rem',
            textDecoration: 'none',
            boxShadow: '0 0 25px rgba(168, 85, 247, 0.5)'
          }}
        >
          Continue to Sign Up <ArrowRight size={16} />
        </a>
      </div>
    </div>
  )
}
