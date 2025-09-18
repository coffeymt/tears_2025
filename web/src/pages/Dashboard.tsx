import React from 'react'
import { useQuery } from '@tanstack/react-query'
import WeekCard from '../components/WeekCard'
import EntryCard, { Entry } from '../components/EntryCard'
import { useAuth } from '../auth/AuthProvider'

async function fetchCurrentWeek() {
  const res = await fetch('/api/weeks/current')
  if (!res.ok) throw new Error('Failed to fetch week')
  return res.json()
}

async function fetchUserEntries(userId: string | number) {
  const res = await fetch(`/api/users/${userId}/entries`)
  if (!res.ok) throw new Error('Failed to fetch entries')
  return res.json()
}

export default function Dashboard() {
  const { user } = useAuth()
  const userId = user?.id

  const weekQuery = useQuery({ queryKey: ['week', 'current'], queryFn: fetchCurrentWeek })
  const entriesQuery = useQuery({
    queryKey: ['entries', userId],
    queryFn: () => fetchUserEntries(userId as string),
    enabled: !!userId,
  })

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>

      {weekQuery.isLoading ? (
        <div>Loading week...</div>
      ) : weekQuery.isError ? (
        <div>Error loading week</div>
      ) : (
        <WeekCard weekNumber={weekQuery.data.week} lock_time={weekQuery.data.lock_time} />
      )}

      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-2">Your Entries</h2>
        {entriesQuery.isLoading ? (
          <div>Loading entries...</div>
        ) : entriesQuery.isError ? (
          <div>Error loading entries</div>
        ) : (
          <div className="space-y-3">
            {entriesQuery.data.map((e: Entry) => (
              <EntryCard key={e.id} entry={e} onMakePicks={() => {}} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
