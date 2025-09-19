import React, { useEffect, useState } from 'react'

type LeaderboardRow = {
  rank: number
  name: string
  score: number
}

export default function LeaderboardTab() {
  const [data, setData] = useState<LeaderboardRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortDesc, setSortDesc] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function fetchBoard() {
      try {
        const res = await fetch('/api/history/leaderboard')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json: LeaderboardRow[] = await res.json()
        if (!cancelled) setData(json)
      } catch (err: any) {
        if (!cancelled) setError(err?.message || 'Failed to load leaderboard')
      }
    }
    fetchBoard()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <div className="text-red-600">{error}</div>
  if (!data) return <div>Loading leaderboard...</div>

  const sorted = [...data].sort((a, b) => (sortDesc ? b.score - a.score : a.score - b.score))

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-medium">Season Leaderboard</h2>
        <button className="px-2 py-1 border rounded" onClick={() => setSortDesc((s) => !s)}>
          Sort: {sortDesc ? 'Descending' : 'Ascending'}
        </button>
      </div>

      <div className="overflow-auto">
        <table className="min-w-full table-auto">
          <thead>
            <tr>
              <th className="text-left p-2">Rank</th>
              <th className="text-left p-2">Entry</th>
              <th className="text-left p-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.rank} className="border-t">
                <td className="p-2">{row.rank}</td>
                <td className="p-2">{row.name}</td>
                <td className="p-2">{row.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
