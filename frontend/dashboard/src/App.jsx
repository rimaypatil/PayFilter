import React, { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import OrganizationSetup from './pages/OrganizationSetup'
import Dashboard from './pages/Dashboard'
import FlaggedQueue from './pages/FlaggedQueue'
import AuditLog from './pages/AuditLog'
import RulesSettings from './pages/RulesSettings'
import KillSwitch from './pages/KillSwitch'
import ApiKeys from './pages/ApiKeys'

function DashboardLayout() {
  const [heldCount, setHeldCount] = useState(0)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      <Sidebar heldCount={heldCount} />
      <main style={{ flex: 1, padding: '2.5rem 3rem', overflowY: 'auto', maxHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/queue" element={<FlaggedQueue onQueueChange={setHeldCount} />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/rules" element={<RulesSettings />} />
          <Route path="/kill-switch" element={<KillSwitch />} />
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/developer" element={<ApiKeys />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

function OrganizationSetupRoute() {
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
          style={{ height: '48px', width: 'auto', objectFit: 'contain' }}
        />
        <span>Verifying organization status...</span>
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (merchantId) {
    return <Navigate to="/" replace />
  }

  return <OrganizationSetup />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/organization-setup" element={<OrganizationSetupRoute />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  )
}
