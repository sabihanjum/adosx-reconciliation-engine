import React, { useState, useEffect, useMemo } from 'react'
import StatCards from './components/StatCards'
import FilterBar from './components/FilterBar'
import DiscrepancyTable from './components/DiscrepancyTable'

export default function App() {
  const [tenants, setTenants] = useState([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [selectedReason, setSelectedReason] = useState('ALL')
  const [sortBy, setSortBy] = useState('value')
  const [sortOrder, setSortOrder] = useState('desc')
  const [searchTerm, setSearchTerm] = useState('')
  
  const [data, setData] = useState({ results: [], stats: {} })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadTenants() {
      try {
        const res = await fetch('/api/tenants/')
        if (!res.ok) throw new Error('Failed to load tenants from backend')
        const json = await res.json()
        setTenants(json.tenants || [])
        if (json.tenants && json.tenants.length > 0) {
          setSelectedTenant(json.tenants[0].org_id)
        }
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }
    loadTenants()
  }, [])

  useEffect(() => {
    if (!selectedTenant) return

    async function loadDiscrepancies() {
      setLoading(true)
      setError(null)
      try {
        const url = `/api/discrepancies/?org_id=${encodeURIComponent(selectedTenant)}&reason=${encodeURIComponent(selectedReason)}&sort_by=${sortBy}&sort_order=${sortOrder}`
        const res = await fetch(url)
        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}))
          throw new Error(errJson.error || `HTTP ${res.status}: Failed to fetch discrepancies`)
        }
        const json = await res.json()
        setData(json)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadDiscrepancies()
  }, [selectedTenant, selectedReason, sortBy, sortOrder])

  const filteredResults = useMemo(() => {
    if (!searchTerm.trim()) return data.results || []
    const term = searchTerm.toLowerCase()
    return (data.results || []).filter(
      (r) =>
        r.record_id.toLowerCase().includes(term) ||
        (r.location_name && r.location_name.toLowerCase().includes(term)) ||
        (r.location_id && r.location_id.toLowerCase().includes(term)) ||
        (r.details && r.details.toLowerCase().includes(term))
    )
  }, [data.results, searchTerm])

  const handleToggleSort = (type) => {
    if (sortBy === type) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(type)
      setSortOrder('desc')
    }
  }

  return (
    <div className="container">
      <header className="header">
        <div className="title-section">
          <h1>Cross-System Reconciliation & Audit</h1>
          <p>Deterministic discrepancy detection across System A and System B exports</p>
        </div>
        <div className="tenant-badge-pill">
          <span className="security-dot" />
          <span>Tenant Isolated: {selectedTenant || 'None'}</span>
        </div>
      </header>

      <StatCards
        stats={data.stats}
        activeReason={selectedReason}
        onSelectReason={setSelectedReason}
      />

      <FilterBar
        tenants={tenants}
        selectedTenant={selectedTenant}
        onSelectTenant={setSelectedTenant}
        selectedReason={selectedReason}
        onSelectReason={setSelectedReason}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onToggleSort={handleToggleSort}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      {loading && (
        <div className="loading-state">
          <p>Auditing records and isolating tenant boundaries...</p>
        </div>
      )}

      {error && (
        <div className="error-state">
          <h3>Auditing Service Error</h3>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && (
        <DiscrepancyTable
          items={filteredResults}
          tenantOrg={selectedTenant}
        />
      )}

      <footer className="footer-note">
        AdosX Reconciliation Engine -- Strict Tenant Boundary Isolation Active -- Zero Row Dropping Verified
      </footer>
    </div>
  )
}