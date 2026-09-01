import React from 'react'
import { useAuth } from '../lib/useAuth'

/**
 * RoleGate Component
 * Convenience UI gate to conditionally hide/disable admin-only controls from analysts.
 * Note: This is a UX convenience — the backend independently enforces RBAC on all endpoints.
 */
export default function RoleGate({ allow = ['admin'], fallback = null, children }) {
  const { role } = useAuth()

  if (!allow.includes(role)) {
    return fallback
  }

  return <>{children}</>
}
