import React from 'react'

export type TeamScore = {
  id: number
  name: string
  score: number | null
}

export type Game = {
  id: number
  home: TeamScore
  away: TeamScore
  status?: string
}

type Props = {
  games: Game[]
}

export default function GamesList({ games }: Props) {
  if (!games || games.length === 0) return <div>No games to show.</div>

  return (
    <div>
      <h2>Games</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {games.map((g) => {
          const homeScore = g.home.score ?? '-'
          const awayScore = g.away.score ?? '-'
          const winner =
            typeof g.home.score === 'number' && typeof g.away.score === 'number'
              ? g.home.score > g.away.score
                ? g.home.name
                : g.away.name
              : null

          return (
            <li key={g.id} style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{g.home.name}</strong> vs <strong>{g.away.name}</strong>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div>{homeScore} — {awayScore}</div>
                  {winner ? <div style={{ fontSize: 12, color: '#666' }}>Winner: {winner}</div> : <div style={{ fontSize: 12, color: '#666' }}>In progress</div>}
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
