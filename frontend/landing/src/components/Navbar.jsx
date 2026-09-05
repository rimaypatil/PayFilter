import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BookOpen, Layers, Key, ExternalLink, Cpu } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()
  const isActive = (path) => location.pathname === path

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      background: 'rgba(7, 10, 18, 0.85)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '0.9rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Brand & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <Link to="/" className="payfilter-brand-link" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }} title="PayFilter Home">
            <img
              src="/payfilter-logo.png"
              alt="PayFilter"
              className="payfilter-brand-logo-full"
            />
            <img
              src="/payfilter-icon.png"
              alt="PayFilter"
              className="payfilter-brand-logo-icon"
            />
          </Link>

          {/* Engine Status Badge */}
          <div className="pulse-badge" style={{ display: 'none', md: 'inline-flex' }}>
            <span className="pulse-dot" />
            <span>AI Risk Firewall</span>
          </div>
        </div>

        {/* Navigation Links (Stitch Aligned) */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Link to="/" style={{
            color: isActive('/') ? '#ffffff' : '#94a3b8',
            background: isActive('/') ? 'rgba(168, 85, 247, 0.12)' : 'transparent',
            border: isActive('/') ? '1px solid rgba(168, 85, 247, 0.25)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '9999px',
            fontWeight: 600,
            fontSize: '0.9rem',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}>
            Product
          </Link>

          <Link to="/how-it-works" style={{
            color: isActive('/how-it-works') ? '#ffffff' : '#94a3b8',
            background: isActive('/how-it-works') ? 'rgba(168, 85, 247, 0.12)' : 'transparent',
            border: isActive('/how-it-works') ? '1px solid rgba(168, 85, 247, 0.25)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '9999px',
            fontWeight: 600,
            fontSize: '0.9rem',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}>
            How It Works
          </Link>

          <Link to="/docs" style={{
            color: isActive('/docs') ? '#ffffff' : '#94a3b8',
            background: isActive('/docs') ? 'rgba(168, 85, 247, 0.12)' : 'transparent',
            border: isActive('/docs') ? '1px solid rgba(168, 85, 247, 0.25)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '9999px',
            fontWeight: 600,
            fontSize: '0.9rem',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}>
            Security
          </Link>

          <Link to="/signup" style={{
            color: isActive('/signup') ? '#ffffff' : '#94a3b8',
            background: isActive('/signup') ? 'rgba(168, 85, 247, 0.12)' : 'transparent',
            border: isActive('/signup') ? '1px solid rgba(168, 85, 247, 0.25)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '9999px',
            fontWeight: 600,
            fontSize: '0.9rem',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}>
            Developers
          </Link>
        </nav>

        {/* Action CTAs: Sign In & Sign Up */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <a
            href="http://localhost:3001/login"
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              padding: '0.5rem 1.1rem',
              borderRadius: '9999px',
              background: 'rgba(255, 255, 255, 0.06)',
              color: '#f8fafc',
              textDecoration: 'none',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transition: 'all 0.2s ease'
            }}
          >
            Sign In
          </a>

          <a
            href="http://localhost:3001/signup"
            style={{
              fontSize: '0.85rem',
              fontWeight: 700,
              padding: '0.55rem 1.25rem',
              borderRadius: '9999px',
              background: 'linear-gradient(135deg, #7c3aed 0%, #9333ea 50%, #c084fc 100%)',
              color: '#ffffff',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              boxShadow: '0 0 20px rgba(168, 85, 247, 0.45)',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              transition: 'all 0.2s ease'
            }}
          >
            Sign Up
          </a>
        </div>
      </div>
    </header>
  )
}
