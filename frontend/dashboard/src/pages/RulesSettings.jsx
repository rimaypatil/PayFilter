import React, { useState, useEffect } from 'react'
import { Sliders, Save, CheckCircle2, AlertTriangle, Shield, Plus, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/useAuth'
import RoleGate from '../components/RoleGate'

export default function RulesSettings() {
  const authContext = useAuth()
  const [maxAmount, setMaxAmount] = useState(50000.0)
  const [maxVelocity, setMaxVelocity] = useState(5)
  const [categoryLimits, setCategoryLimits] = useState({})
  const [newCategory, setNewCategory] = useState('')
  const [newCategoryLimit, setNewCategoryLimit] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchCurrentRules() {
      try {
        const rules = await api.getRules(authContext)
        setMaxAmount(rules.max_amount_per_order || 50000.0)
        setMaxVelocity(rules.max_transactions_per_minute || 5)
        setCategoryLimits(rules.category_limits || {})
      } catch (err) {
        console.error('Failed to load rules:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchCurrentRules()
  }, [authContext.merchantId])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSavedSuccess(false)

    try {
      await api.updateRules(authContext, {
        max_amount_per_order: parseFloat(maxAmount),
        max_transactions_per_minute: parseInt(maxVelocity, 10),
        category_limits: categoryLimits,
      })
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3500)
    } catch (err) {
      setError(err.message || 'Failed to update rules')
    } finally {
      setSaving(false)
    }
  }

  const handleAddCategory = () => {
    if (!newCategory.trim() || !newCategoryLimit) return
    setCategoryLimits(prev => ({
      ...prev,
      [newCategory.trim().toLowerCase()]: parseFloat(newCategoryLimit),
    }))
    setNewCategory('')
    setNewCategoryLimit('')
  }

  const handleRemoveCategory = (cat) => {
    setCategoryLimits(prev => {
      const copy = { ...prev }
      delete copy[cat]
      return copy
    })
  }

  return (
    <RoleGate
      allow={['admin']}
      fallback={
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', maxWidth: '600px', margin: '3rem auto' }}>
          <AlertTriangle size={36} color="#fbbf24" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
            Admin Privileges Required
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Rules configuration can only be edited by users with the <strong>Admin</strong> role. Your current role is <strong>{authContext.role}</strong>.
          </p>
        </div>
      }
    >
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <Sliders size={24} color="#818cf8" />
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
              Merchant Risk Rules & Caps
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
            Configure deterministic hard caps and category limits evaluated prior to ML scoring.
          </p>
        </div>

        {savedSuccess && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            borderRadius: '8px',
            padding: '0.85rem 1rem',
            marginBottom: '1.5rem',
            color: '#6ee7b7',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <CheckCircle2 size={18} /> Rules updated successfully and recorded to audit trail.
          </div>
        )}

        {error && (
          <div style={{
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: '8px',
            padding: '0.85rem 1rem',
            marginBottom: '1.5rem',
            color: '#fb7185',
            fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSave}>
          <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '1.25rem' }}>
              Global Order & Velocity Limits
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Max Amount Per Order (₹)
                </label>
                <input
                  type="number"
                  step="100"
                  value={maxAmount}
                  onChange={(e) => setMaxAmount(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem 0.85rem',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.35rem', display: 'block' }}>
                  Orders exceeding this threshold are blocked immediately.
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.4rem' }}>
                  Max Velocity (Transactions / Minute)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={maxVelocity}
                  onChange={(e) => setMaxVelocity(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem 0.85rem',
                    borderRadius: '8px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.35rem', display: 'block' }}>
                  Prevents automated runaway loops from draining balances.
                </span>
              </div>
            </div>

            {/* CATEGORY LIMITS */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
                Category-Specific Caps
              </h3>
              <p style={{ color: '#94a3b8', fontSize: '0.8rem', marginBottom: '1rem' }}>
                Set custom maximum order thresholds for specific merchant categories.
              </p>

              {/* Existing category caps */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                {Object.entries(categoryLimits).map(([cat, lim]) => (
                  <div key={cat} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(0,0,0,0.3)',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <span style={{ fontWeight: 600, color: '#cbd5e1', textTransform: 'capitalize' }}>{cat}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ color: '#818cf8', fontWeight: 700 }}>₹{Number(lim).toLocaleString()}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCategory(cat)}
                        style={{ background: 'transparent', border: 'none', color: '#f43f5e', cursor: 'pointer' }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add category input */}
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <input
                  type="text"
                  placeholder="Category (e.g. gaming, crypto)"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
                <input
                  type="number"
                  placeholder="Max Limit (₹)"
                  value={newCategoryLimit}
                  onChange={(e) => setNewCategoryLimit(e.target.value)}
                  style={{
                    width: '160px',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '6px',
                    background: 'rgba(0,0,0,0.4)',
                    border: '1px solid var(--border-subtle)',
                    color: '#ffffff',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddCategory}
                  style={{
                    padding: '0.65rem 1rem',
                    borderRadius: '6px',
                    background: 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    color: '#a5b4fc',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem'
                  }}
                >
                  <Plus size={15} /> Add
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '0.85rem 2rem',
              borderRadius: '8px',
              background: saving ? '#475569' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.95rem',
              border: 'none',
              cursor: saving ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              boxShadow: '0 4px 15px rgba(99, 102, 241, 0.35)'
            }}
          >
            <Save size={16} /> {saving ? 'Saving Rules...' : 'Save Rules Configuration'}
          </button>
        </form>
      </div>
    </RoleGate>
  )
}
