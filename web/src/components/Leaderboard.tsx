import React from 'react'

type Row = {
  rank: number
  entry_id?: number
  entry_name: string
  score: number
}

type Props = {
  leaderboard: Row[]
  currentEntryId?: number | null
}

export default function Leaderboard({ leaderboard, currentEntryId }: Props) {
  if (!leaderboard || leaderboard.length === 0) return <div>No leaderboard data.</div>

  return (
    <div>
      <h2>Leaderboard</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '1px solid #ddd' }}>
            <th style={{ width: 60 }}>Rank</th>
            <th>Entry</th>
            <th style={{ width: 100, textAlign: 'right' }}>Score</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map((r) => {
            const isCurrent = currentEntryId != null && r.entry_id === currentEntryId
            return (
              <tr key={r.entry_id ?? r.rank} style={{ background: isCurrent ? '#fffbeb' : 'transparent' }}>
                <td style={{ padding: '8px 4px' }}>{r.rank}</td>
                <td style={{ padding: '8px 4px' }}>{r.entry_name}</td>
                <td style={{ padding: '8px 4px', textAlign: 'right' }}>{r.score}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
