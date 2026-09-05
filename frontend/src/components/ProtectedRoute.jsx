import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/useAuth'

export default function ProtectedRoute({ children }) {
  const { session, loading, merchantId } = useAuth()

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1.25rem',
        background: '#070a12',
        color: '#818cf8',
        fontFamily: 'var(--font-sans)',
        fontSize: '0.95rem'
      }}>
        <img
          src="/payfilter-icon.png"
          alt="PayFilter"
          className="pulse-logo-icon"
          style={{
            height: '48px',
            width: 'auto',
            objectFit: 'contain'
          }}
        />
        <span>Authenticating PayFilter session...</span>
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (!merchantId) {
    return <Navigate to="/organization-setup" replace />
  }

  return children
}
