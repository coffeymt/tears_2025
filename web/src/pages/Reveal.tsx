import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import useSiteTime from '../hooks/useSiteTime'
import GamesList from '../components/GamesList'
import DistributionChart from '../components/DistributionChart'
import Leaderboard from '../components/Leaderboard'

type RevealData = {
  games: any[]
  distribution?: any
  leaderboard?: any[]
}

async function fetchWeek(weekId: string) {
  const res = await fetch(`${window.location.origin}/api/weeks/${weekId}`)
  if (!res.ok) throw new Error('Failed to load week')
  return res.json()
}

async function fetchRevealSnapshot(weekId: string) {
  const res = await fetch(`${window.location.origin}/api/weeks/${weekId}/reveal-snapshot`)
  if (!res.ok) throw new Error('Failed to load reveal snapshot')
  return res.json() as Promise<RevealData>
}

export default function RevealPage() {
  const { weekId } = useParams<{ weekId: string }>()
  const { now } = useSiteTime()

  type Week = { id: number; lock_time?: string }
  const weekQ = useQuery<Week, Error>({ queryKey: ['week', weekId], queryFn: () => fetchWeek(weekId || ''), enabled: !!weekId })

  const lockTime = weekQ.data?.lock_time ? new Date(weekQ.data.lock_time).getTime() : undefined
  const unlocked = typeof lockTime === 'number' ? now.getTime() >= lockTime : false

  const revealQ = useQuery<RevealData, Error>({ queryKey: ['weekReveal', weekId], queryFn: () => fetchRevealSnapshot(weekId || ''), enabled: !!weekId && unlocked })

  if (weekQ.isLoading) return <div>Loading week...</div>
  if (weekQ.isError) return <div>Error loading week</div>

  if (!unlocked) {
    return (
      <div>
        <h1>Reveal for Week {weekId}</h1>
        <p>This page is locked until the week's lock time.</p>
      </div>
    )
  }

  if (revealQ.isLoading) return <div>Loading reveal data...</div>
  if (revealQ.isError) return <div>Error loading reveal data</div>

  const data = revealQ.data as RevealData

  return (
    <div>
      <h1>Reveal for Week {weekId}</h1>
      <section>
        <GamesList games={data?.games || []} />
      </section>

      <section>
        {data?.distribution ? <DistributionChart distribution={data.distribution} /> : <div>No distribution available.</div>}
      </section>

      <section>
        <Leaderboard leaderboard={data?.leaderboard || []} currentEntryId={null} />
      </section>
    </div>
  )
}
