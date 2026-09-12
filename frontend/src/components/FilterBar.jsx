import React from 'react'

export default function FilterBar({
  tenants,
  selectedTenant,
  onSelectTenant,
  selectedReason,
  onSelectReason,
  sortBy,
  sortOrder,
  onToggleSort,
  searchTerm,
  onSearchChange,
}) {
  return (
    <div className="controls-card">
      <div className="control-group">
        <label className="control-label">Tenant Isolation:</label>
        <select
          className="select-input font-mono"
          value={selectedTenant}
          onChange={(e) => onSelectTenant(e.target.value)}
        >
          {tenants.map((t) => (
            <option key={t.org_id} value={t.org_id}>
              {t.org_id} ({t.locations.length} Locations)
            </option>
          ))}
        </select>
      </div>

      <div className="control-group">
        <label className="control-label">Discrepancy Class:</label>
        <select
          className="select-input"
          value={selectedReason}
          onChange={(e) => onSelectReason(e.target.value)}
        >
          <option value="ALL">All Discrepancies</option>
          <option value="VALUE_MISMATCH">Value Mismatch</option>
          <option value="DUPLICATE_IN_SYSTEM_B">Duplicate in System B</option>
          <option value="MISSING_IN_SYSTEM_B">Missing in System B</option>
          <option value="ORPHAN_IN_SYSTEM_B">Orphan in System B</option>
        </select>
      </div>

      <div className="control-group">
        <input
          type="text"
          className="text-input"
          placeholder="Filter by Ref or Location..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="control-group">
        <button
          className={`sort-btn ${sortBy === 'value' ? 'active' : ''}`}
          onClick={() => onToggleSort('value')}
        >
          Sort by Value {sortBy === 'value' ? (sortOrder === 'asc' ? '^ (Asc)' : 'v (Desc)') : ''}
        </button>
        <button
          className={`sort-btn ${sortBy === 'record_id' ? 'active' : ''}`}
          onClick={() => onToggleSort('record_id')}
        >
          Sort by ID {sortBy === 'record_id' ? (sortOrder === 'asc' ? '^' : 'v') : ''}
        </button>
      </div>
    </div>
  )
}