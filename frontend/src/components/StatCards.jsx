import React from 'react'

export default function StatCards({ stats, activeReason, onSelectReason }) {
  if (!stats) return null

  const cards = [
    { key: 'ALL', label: 'All Discrepancies', count: stats.ALL || 0 },
    { key: 'VALUE_MISMATCH', label: 'Value Mismatches', count: stats.VALUE_MISMATCH || 0 },
    { key: 'DUPLICATE_IN_SYSTEM_B', label: 'Duplicates in B', count: stats.DUPLICATE_IN_SYSTEM_B || 0 },
    { key: 'MISSING_IN_SYSTEM_B', label: 'Missing in B', count: stats.MISSING_IN_SYSTEM_B || 0 },
    { key: 'ORPHAN_IN_SYSTEM_B', label: 'Orphans in B', count: stats.ORPHAN_IN_SYSTEM_B || 0 },
  ]

  return (
    <div className="stats-grid">
      {cards.map(c => (
        <div
          key={c.key}
          className={`stat-card ${activeReason === c.key ? 'active' : ''}`}
          onClick={() => onSelectReason(c.key)}
        >
          <div className="label">{c.label}</div>
          <div className="value">{c.count}</div>
        </div>
      ))}
    </div>
  )
}