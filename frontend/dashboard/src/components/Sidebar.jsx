import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  Sliders,
  Power,
  LogOut,
  Shield,
  User,
  UserCheck
} from 'lucide-react'
import { useAuth } from '../lib/useAuth'
import RoleGate from './RoleGate'

export default function Sidebar({ heldCount = 0 }) {
  const location = useLocation()
  const { user, role, merchantId, logout, setRole } = useAuth()

  const isActive = (path) => location.pathname === path

  const navItems = [
    { label: 'Live Overview', path: '/', icon: LayoutDashboard },
    { label: 'Flagged Queue', path: '/queue', icon: AlertTriangle, badge: heldCount },
    { label: 'Audit Trail', path: '/audit', icon: FileText },
  ]

  const adminNavItems = [
    { label: 'Rules & Caps', path: '/rules', icon: Sliders, adminOnly: true },
    { label: 'Kill Switch', path: '/kill-switch', icon: Power, adminOnly: true, danger: true },
  ]

  return (
    <aside style={{
      width: '260px',
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '1.5rem 1rem',
      height: '100vh',
      position: 'sticky',
      top: 0
    }}>
      <div>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', padding: '0 0.5rem 1.5rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '1.5rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Shield size={18} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ffffff' }}>
              Pay<span style={{ color: '#818cf8' }}>Filter</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Merchant Console</div>
          </div>
        </div>

        {/* Standard Navigation */}
        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 0.5rem 0.5rem' }}>
          Monitoring
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '1.5rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '8px',
                  background: active ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  color: active ? '#818cf8' : '#94a3b8',
                  fontWeight: active ? 700 : 500,
                  fontSize: '0.88rem',
                  textDecoration: 'none',
                  border: active ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                  transition: 'all 0.15s'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <Icon size={17} color={active ? '#818cf8' : '#94a3b8'} />
                  {item.label}
                </div>
                {item.badge > 0 && (
                  <span style={{
                    background: '#f59e0b',
                    color: '#000000',
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '0.1rem 0.45rem',
                    borderRadius: '9999px'
                  }}>
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Admin Navigation */}
        <RoleGate allow={['admin']}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 0.5rem 0.5rem' }}>
            Administration
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {adminNavItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.65rem',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '8px',
                    background: active ? (item.danger ? 'rgba(244, 63, 94, 0.15)' : 'rgba(99, 102, 241, 0.15)') : 'transparent',
                    color: active ? (item.danger ? '#f87171' : '#818cf8') : (item.danger ? '#fca5a5' : '#94a3b8'),
                    fontWeight: active ? 700 : 500,
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    border: active ? (item.danger ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid rgba(99, 102, 241, 0.3)') : '1px solid transparent',
                    transition: 'all 0.15s'
                  }}
                >
                  <Icon size={17} />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </RoleGate>
      </div>

      {/* User Info & Role Switcher */}
      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', padding: '0 0.25rem' }}>
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }}>
              {user?.email || 'operator@acme.com'}
            </div>
            <div style={{ fontSize: '0.7rem', color: role === 'admin' ? '#818cf8' : '#34d399', fontWeight: 600 }}>
              Role: {role.toUpperCase()}
            </div>
          </div>

          <button
            onClick={logout}
            title="Log out"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              padding: '0.4rem',
              borderRadius: '6px'
            }}
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Role Demo Toggle */}
        <div style={{
          background: 'rgba(0,0,0,0.4)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '6px',
          padding: '0.35rem',
          display: 'flex',
          gap: '0.25rem'
        }}>
          <button
            onClick={() => setRole('admin')}
            style={{
              flex: 1,
              padding: '0.25rem',
              borderRadius: '4px',
              border: 'none',
              background: role === 'admin' ? '#6366f1' : 'transparent',
              color: role === 'admin' ? '#ffffff' : '#94a3b8',
              fontSize: '0.7rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Admin
          </button>

          <button
            onClick={() => setRole('analyst')}
            style={{
              flex: 1,
              padding: '0.25rem',
              borderRadius: '4px',
              border: 'none',
              background: role === 'analyst' ? '#10b981' : 'transparent',
              color: role === 'analyst' ? '#ffffff' : '#94a3b8',
              fontSize: '0.7rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Analyst
          </button>
        </div>
      </div>
    </aside>
  )
}
