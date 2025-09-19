import React, { useEffect, useState } from 'react'

type TeamUsageRow = {
  team: string
  picks: number
}

export default function TeamUsageTab() {
  const [data, setData] = useState<TeamUsageRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchUsage() {
      try {
        const res = await fetch('/api/history/team-usage')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json: TeamUsageRow[] = await res.json()
        if (!cancelled) setData(json)
      } catch (err: any) {
        if (!cancelled) setError(err?.message || 'Failed to load team usage')
      }
    }
    fetchUsage()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <div className="text-red-600">{error}</div>
  if (!data) return <div>Loading team usage...</div>

  const total = data.reduce((s, r) => s + r.picks, 0) || 1

  return (
    <div>
      <h2 className="text-lg font-medium mb-3">Team Usage</h2>
      <div className="overflow-auto">
        <table className="min-w-full table-auto">
          <thead>
            <tr>
              <th className="text-left p-2">Team</th>
              <th className="text-left p-2">Picks</th>
              <th className="text-left p-2">%</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.team} className="border-t">
                <td className="p-2">{row.team}</td>
                <td className="p-2">{row.picks}</td>
                <td className="p-2">{((row.picks / total) * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
