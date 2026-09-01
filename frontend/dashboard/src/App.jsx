import React, { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './lib/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import FlaggedQueue from './pages/FlaggedQueue'
import AuditLog from './pages/AuditLog'
import RulesSettings from './pages/RulesSettings'
import KillSwitch from './pages/KillSwitch'

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
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
