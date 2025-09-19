import React from 'react'
import { useParams } from 'react-router-dom'
import GamesEditor from './GamesEditor'

export default function WeekGamesPage() {
  const params = useParams()
  const weekId = Number(params.weekId)
  if (Number.isNaN(weekId)) return <p>Invalid week id</p>
  return (
    <div>
      <GamesEditor weekId={weekId} />
    </div>
  )
}
