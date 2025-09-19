import React from 'react'

type Props = {
  open: boolean
  team?: { id: number; city?: string; nickname?: string; name?: string }
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmPickModal({ open, team, onConfirm, onCancel }: Props) {
  if (!open) return null

  return (
    <div data-testid="confirm-pick-modal" style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.4)' }}>
      <div style={{ background: '#fff', padding: 16, borderRadius: 8, width: 400 }}>
        <h3>Confirm Pick</h3>
        <div style={{ margin: '12px 0' }}>
          <strong>{team ? (team.city ? `${team.city} ` : '') + (team.nickname || team.name) : 'No team selected'}</strong>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button data-testid="confirm-pick-cancel" onClick={onCancel}>Cancel</button>
          <button data-testid="confirm-pick-confirm" onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  )
}
