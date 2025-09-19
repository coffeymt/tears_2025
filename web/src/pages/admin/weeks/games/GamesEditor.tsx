import React, { useState } from 'react'
import GamesTableEditor from './GamesTableEditor'

type Props = {
  weekId: number
}

export default function GamesEditor({ weekId }: Props) {
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  async function handleSync() {
    setSyncing(true)
    setMessage(null)
    try {
      const res = await fetch('/internal/sync-games/espn', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ week_id: weekId }) })
      const text = await res.text()
      let json: any = null
      try {
        json = text ? JSON.parse(text) : null
      } catch (_) {
        json = null
      }
      if (!res.ok) {
        const serverMsg = json?.message || text || res.statusText
        throw new Error(String(serverMsg || 'Sync failed'))
      }
      const successMsg = json?.message || 'Sync started'
      setMessage(successMsg)
    } catch (err:any) {
      setMessage('Sync failed: ' + (err?.message ?? String(err)))
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Manage Games for Week {weekId}</h3>
      <p className="mb-4 text-sm text-gray-600">This page will list games and allow editing scores and syncing with ESPN.</p>
      <div className="flex gap-2">
        <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={handleSync} disabled={syncing} data-testid="sync-button">
          {syncing ? 'Syncing...' : 'Sync from ESPN'}
        </button>
        <button className="px-3 py-1 border rounded" onClick={() => alert('Add Game - not implemented')}>Add Game</button>
      </div>
      {message && <p className="mt-3 text-sm">{message}</p>}

      <div className="mt-6">
        <GamesTableEditor weekId={weekId} />
      </div>
    </div>
  )
}
