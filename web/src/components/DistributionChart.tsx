import React from 'react'

/*
  Simple, dependency-free bar chart for pick distribution.
  Assumed `distribution` shape:
  {
    games: [
      {
        gameId: number,
        labels: [string], // team names
        counts: [number]  // parallel array of counts per label
      }
    ]
  }

  The component renders one small grouped bar chart per game. It's intentionally minimal so we avoid adding `recharts` as a dependency for now.
*/

type GameDist = {
  gameId: number
  labels: string[]
  counts: number[]
}

type Props = {
  distribution: { games: GameDist[] } | null | undefined
}

export default function DistributionChart({ distribution }: Props) {
  if (!distribution || !distribution.games || distribution.games.length === 0) return <div>No distribution data.</div>

  return (
    <div>
      <h2>Pick Distribution</h2>
      <div style={{ display: 'grid', gap: 16 }}>
        {distribution.games.map((g) => {
          const total = g.counts.reduce((a, b) => a + b, 0) || 1
          return (
            <div key={g.gameId} style={{ border: '1px solid #eee', padding: 8 }}>
              <div style={{ fontSize: 14, marginBottom: 6 }}>Game {g.gameId}</div>
              <div>
                {g.labels.map((label, i) => {
                  const pct = Math.round((g.counts[i] / total) * 100)
                  return (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                      <div style={{ width: 120 }}>{label}</div>
                      <div style={{ flex: 1, margin: '0 8px', background: '#f3f3f3' }}>
                        <div style={{ width: `${pct}%`, background: '#60a5fa', height: 12 }} />
                      </div>
                      <div style={{ width: 48, textAlign: 'right' }}>{g.counts[i]} ({pct}%)</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
