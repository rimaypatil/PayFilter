import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/useAuth'

export default function ProtectedRoute({ children }) {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#070a12',
        color: '#818cf8',
        fontFamily: 'var(--font-sans)',
        fontSize: '1rem'
      }}>
        Authenticating PayFilter session...
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  return children
}
