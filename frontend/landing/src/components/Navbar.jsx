import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, BookOpen, Layers, Key, ExternalLink, Cpu } from 'lucide-react'

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
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <Shield size={22} color="#ffffff" />
            </div>
            <div>
              <span style={{ fontSize: '1.35rem', fontWeight: 900, color: '#ffffff', letterSpacing: '-0.03em' }}>
                Pay<span style={{ color: '#818cf8' }}>Filter</span>
              </span>
            </div>
          </Link>

          {/* Engine Status Badge */}
          <div className="pulse-badge" style={{ display: 'none', md: 'inline-flex' }}>
            <span className="pulse-dot" />
            <span>AI Risk Firewall</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Link to="/" style={{
            color: isActive('/') ? '#ffffff' : '#94a3b8',
            background: isActive('/') ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            border: isActive('/') ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '0.88rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s'
          }}>
            <Layers size={15} /> Overview
          </Link>

          <Link to="/how-it-works" style={{
            color: isActive('/how-it-works') ? '#ffffff' : '#94a3b8',
            background: isActive('/how-it-works') ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            border: isActive('/how-it-works') ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '0.88rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s'
          }}>
            <Cpu size={15} /> Architecture
          </Link>

          <Link to="/docs" style={{
            color: isActive('/docs') ? '#ffffff' : '#94a3b8',
            background: isActive('/docs') ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            border: isActive('/docs') ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
            padding: '0.45rem 0.9rem',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '0.88rem',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s'
          }}>
            <BookOpen size={15} /> API Docs
          </Link>
        </nav>

        {/* Action CTAs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.86rem',
              fontWeight: 600,
              padding: '0.55rem 1rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#cbd5e1',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.2s'
            }}
          >
            Dashboard Login <ExternalLink size={13} color="#94a3b8" />
          </a>

          <Link
            to="/signup"
            style={{
              fontSize: '0.86rem',
              fontWeight: 700,
              padding: '0.55rem 1.15rem',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#ffffff',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.2s'
            }}
          >
            <Key size={14} /> Get API Key
          </Link>
        </div>
      </div>
    </header>
  )
}
