import React, { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Footer from './components/Footer'

// Landing & Informational Pages
import Home from './pages/Home'
import HowItWorks from './pages/HowItWorks'
import Docs from './pages/Docs'

// Authentication & Onboarding Pages
import Login from './pages/Login'
import SignUp from './pages/SignUp'
import OrganizationSetup from './pages/OrganizationSetup'

// Dashboard Console Pages
import Dashboard from './pages/Dashboard'
import FlaggedQueue from './pages/FlaggedQueue'
import AuditLog from './pages/AuditLog'
import RulesSettings from './pages/RulesSettings'
import KillSwitch from './pages/KillSwitch'
import ApiKeys from './pages/ApiKeys'

/**
 * Public Landing Layout with PayFilter Navbar and Footer
 */
function LandingLayout({ children }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-dark)' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        {children}
      </main>
      <Footer />
    </div>
  )
}

/**
 * Protected Merchant Dashboard Layout with Sidebar and Main Console Viewport
 */
function DashboardLayout() {
  const [heldCount, setHeldCount] = useState(0)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      <Sidebar heldCount={heldCount} />
      <main style={{ flex: 1, padding: '2.5rem 3rem', overflowY: 'auto', maxHeight: '100vh' }}>
        <Routes>
          {/* Main Dashboard Overviews */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/transactions" element={<Dashboard />} />

          {/* Review & Flagged Queue */}
          <Route path="/queue" element={<FlaggedQueue onQueueChange={setHeldCount} />} />
          <Route path="/review-queue" element={<FlaggedQueue onQueueChange={setHeldCount} />} />

          {/* Audit Trail */}
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/audit-log" element={<AuditLog />} />

          {/* Rules & Risk Engine */}
          <Route path="/rules" element={<RulesSettings />} />
          <Route path="/risk-engine" element={<RulesSettings />} />

          {/* Security & Kill Switch */}
          <Route path="/kill-switch" element={<KillSwitch />} />
          <Route path="/security" element={<KillSwitch />} />

          {/* Developer & API Keys */}
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/developer" element={<ApiKeys />} />

          {/* Fallback for undefined dashboard subroutes */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

/**
 * Route Guard for Organization Setup
 * Unauthenticated -> /login
 * Authenticated + already has merchant -> /dashboard
 * Authenticated + no merchant -> OrganizationSetup
 */
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
    return <Navigate to="/dashboard" replace />
  }

  return <OrganizationSetup />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Landing Page Routes */}
        <Route path="/" element={<Navigate to="/landing" replace />} />
        <Route
          path="/landing"
          element={
            <LandingLayout>
              <Home />
            </LandingLayout>
          }
        />
        <Route
          path="/how-it-works"
          element={
            <LandingLayout>
              <HowItWorks />
            </LandingLayout>
          }
        />
        <Route
          path="/docs"
          element={
            <LandingLayout>
              <Docs />
            </LandingLayout>
          }
        />

        {/* Authentication & Onboarding Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/organization-setup" element={<OrganizationSetupRoute />} />

        {/* Unified Dashboard Routes */}
        <Route
          path="/dashboard/*"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        />

        {/* Global Fallback */}
        <Route path="*" element={<Navigate to="/landing" replace />} />
      </Routes>
    </AuthProvider>
  )
}
