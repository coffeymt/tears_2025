import React from 'react'

export type Team = { id: number; city?: string; nickname?: string; name?: string }

type Props = {
  teams: Team[]
  // accept either a Set<number> or an array of numbers for convenience
  usedTeamIds?: Set<number> | number[]
  onSelect?: (team: Team) => void
}

export default function TeamGrid({ teams, usedTeamIds = new Set(), onSelect }: Props) {
  // normalize usedTeamIds to a Set for O(1) lookups
  const usedSet = Array.isArray(usedTeamIds) ? new Set(usedTeamIds) : usedTeamIds

  return (
    <div data-testid="team-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
      {teams.map((t) => {
        const used = usedSet.has(t.id)
        return (
          <button
            key={t.id}
            data-testid={`team-grid-item-${t.id}`}
            onClick={() => !used && onSelect && onSelect(t)}
            disabled={used}
            aria-disabled={used}
            title={used ? 'This team has already been used for this entry' : `Select ${t.nickname || t.name}`}
            style={{
              padding: 8,
              border: '1px solid #ddd',
              borderRadius: 6,
              background: used ? '#f3f3f3' : '#fff',
              cursor: used ? 'not-allowed' : 'pointer',
              textAlign: 'left',
            }}
          >
            <div>{t.city ? `${t.city} ` : ''}{t.nickname || t.name}</div>
            {used && <div data-testid={`team-grid-used-${t.id}`} style={{ color: '#666', fontSize: 12 }}>Used</div>}
          </button>
        )
      })}
    </div>
  )
}
