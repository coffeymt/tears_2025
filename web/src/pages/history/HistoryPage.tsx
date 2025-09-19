import React, { useState } from 'react'
import HistoryMatrix from './HistoryMatrix'
import LeaderboardTab from './LeaderboardTab'
import TeamUsageTab from './TeamUsageTab'

function MatrixTab() {
  return (
    <div>
      <HistoryMatrix />
    </div>
  )
}

// Real LeaderboardTab and TeamUsageTab components are imported from their files.

export default function HistoryPage() {
  const [active, setActive] = useState<'matrix' | 'leaderboard' | 'usage'>('matrix')

  return (
    <div className="p-4">
      <h1 className="text-2xl font-semibold mb-4">History</h1>
      <div className="mb-4">
        <nav className="flex space-x-2">
          <button className={`px-3 py-1 rounded ${active === 'matrix' ? 'bg-blue-600 text-white' : 'border'}`} onClick={() => setActive('matrix')}>
            Matrix
          </button>
          <button className={`px-3 py-1 rounded ${active === 'leaderboard' ? 'bg-blue-600 text-white' : 'border'}`} onClick={() => setActive('leaderboard')}>
            Leaderboard
          </button>
          <button className={`px-3 py-1 rounded ${active === 'usage' ? 'bg-blue-600 text-white' : 'border'}`} onClick={() => setActive('usage')}>
            Team Usage
          </button>
        </nav>
      </div>

      <div className="bg-white p-4 rounded shadow">
        {active === 'matrix' && <MatrixTab />}
  {active === 'leaderboard' && <LeaderboardTab />}
  {active === 'usage' && <TeamUsageTab />}
      </div>
    </div>
  )
}
