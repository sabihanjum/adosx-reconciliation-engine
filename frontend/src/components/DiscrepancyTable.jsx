import React from 'react'

export default function DiscrepancyTable({ items, tenantOrg }) {
  const getBadgeClass = (reason) => `badge badge-${reason}`

  const formatReasonLabel = (reason) => {
    switch (reason) {
      case 'MISSING_IN_SYSTEM_B':
        return 'Missing in B'
      case 'ORPHAN_IN_SYSTEM_B':
        return 'Orphan in B'
      case 'DUPLICATE_IN_SYSTEM_B':
        return 'Duplicate in B'
      case 'VALUE_MISMATCH':
        return 'Value Mismatch'
      default:
        return reason
    }
  }

  const formatCurrency = (val) => {
    if (val === null || val === undefined || val === '') return '---'
    return val
  }

  if (items.length === 0) {
    return (
      <div className="table-wrapper">
        <div className="empty-state">
          <h3>No Discrepancies Found</h3>
          <p>All records for tenant <strong>{tenantOrg}</strong> align under the selected filters.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="table-wrapper">
      <div className="table-header-info">
        <span>Showing {items.length} reconciled discrepancy rows</span>
        <span className="font-mono" style={{ color: '#059669' }}>
          Boundary Guard: Active (Org: {tenantOrg})
        </span>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Discrepancy Reason</th>
            <th>Record Identifier</th>
            <th>Location</th>
            <th>Tenant</th>
            <th>System A Value</th>
            <th>System B Value</th>
            <th>Audit Notes</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row, idx) => {
            const isMismatch = row.reason === 'VALUE_MISMATCH'
            return (
              <tr key={`${row.record_id}-${idx}`}>
                <td>
                  <span className={getBadgeClass(row.reason)}>
                    {formatReasonLabel(row.reason)}
                  </span>
                </td>
                <td className="font-mono" style={{ fontWeight: 600 }}>
                  {row.record_id}
                </td>
                <td>
                  <div>{row.location_name}</div>
                  <div className="font-mono" style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    {row.location_id}
                  </div>
                </td>
                <td>
                  <span className="font-mono" style={{ fontSize: '0.8rem', background: '#f1f5f9', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                    {row.org_id}
                  </span>
                </td>
                <td>
                  <span className={`val-box font-mono ${isMismatch ? 'val-mismatch-a' : ''}`}>
                    {formatCurrency(row.val_a)}
                  </span>
                </td>
                <td>
                  <span className={`val-box font-mono ${isMismatch ? 'val-mismatch-b' : ''}`}>
                    {formatCurrency(row.val_b)}
                  </span>
                </td>
                <td className="details-text">
                  {row.details}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}