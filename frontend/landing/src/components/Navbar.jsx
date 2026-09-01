import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, ArrowRight, Terminal, BookOpen, Layers, UserPlus } from 'lucide-react'

export default function Navbar() {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(16px)',
      background: 'rgba(9, 13, 22, 0.8)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '1rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            <Shield size={20} color="#ffffff" />
          </div>
          <div>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              Pay<span style={{ color: '#818cf8' }}>Filter</span>
            </span>
            <span style={{
              marginLeft: '0.5rem',
              fontSize: '0.65rem',
              fontWeight: 700,
              padding: '0.15rem 0.4rem',
              borderRadius: '9999px',
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#a5b4fc',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              textTransform: 'uppercase'
            }}>
              Risk Engine
            </span>
          </div>
        </Link>

        {/* Navigation links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <Link to="/" style={{
            color: isActive('/') ? '#ffffff' : '#94a3b8',
            fontWeight: isActive('/') ? 600 : 500,
            fontSize: '0.9rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'color 0.2s'
          }}>
            <Layers size={16} /> Home
          </Link>

          <Link to="/how-it-works" style={{
            color: isActive('/how-it-works') ? '#ffffff' : '#94a3b8',
            fontWeight: isActive('/how-it-works') ? 600 : 500,
            fontSize: '0.9rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'color 0.2s'
          }}>
            <Shield size={16} /> How It Works
          </Link>

          <Link to="/docs" style={{
            color: isActive('/docs') ? '#ffffff' : '#94a3b8',
            fontWeight: isActive('/docs') ? 600 : 500,
            fontSize: '0.9rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'color 0.2s'
          }}>
            <BookOpen size={16} /> API Docs
          </Link>
        </nav>

        {/* Action CTAs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              padding: '0.55rem 1rem',
              borderRadius: '8px',
              background: 'transparent',
              color: '#cbd5e1',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
          >
            Dashboard Login
          </a>

          <Link
            to="/signup"
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              padding: '0.55rem 1.1rem',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)',
              transition: 'all 0.2s'
            }}
          >
            <UserPlus size={15} /> Get API Key
          </Link>
        </div>
      </div>
    </header>
  )
}
