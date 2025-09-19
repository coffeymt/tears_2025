import React from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import TeamGrid, { Team as TeamType } from '../components/TeamGrid'
import ConfirmPickModal from '../components/ConfirmPickModal'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

type Pick = { id: number; week: number; team_id: number }

async function fetchTeams(): Promise<TeamType[]> {
  const res = await fetch(`${window.location.origin}/api/teams`)
  if (!res.ok) throw new Error('Failed to load teams')
  return res.json()
}

async function fetchPicks(entryId: string): Promise<Pick[]> {
  const res = await fetch(`${window.location.origin}/api/entries/${entryId}/picks`)
  if (!res.ok) throw new Error('Failed to load picks')
  return res.json()
}

export default function Picks() {
  const { entryId } = useParams<{ entryId: string }>()
  const [selectedTeam, setSelectedTeam] = useState<TeamType | undefined>(undefined)
  const [modalOpen, setModalOpen] = useState(false)

  const teamsQ = useQuery<TeamType[], Error>({ queryKey: ['teams'], queryFn: fetchTeams })
  const picksQ = useQuery<Pick[], Error>({
    queryKey: ['entryPicks', entryId],
    queryFn: () => fetchPicks(entryId || ''),
    enabled: !!entryId,
  })
  const queryClient = useQueryClient()

  type SubmitVars = { entryId: string; teamId: number }
  type Context = { previous?: Pick[] }

  const submitPickMutation = useMutation<Pick, Error, SubmitVars, Context>({
    mutationFn: async ({ entryId, teamId }: SubmitVars) => {
      const res = await fetch(`${window.location.origin}/api/picks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entry_id: Number(entryId), team_id: teamId }),
      })
      if (!res.ok) throw new Error('Failed to submit pick')
      return res.json()
    },
    onMutate: async (vars: SubmitVars) => {
      await queryClient.cancelQueries({ queryKey: ['entryPicks', vars.entryId] })
      const previous = queryClient.getQueryData<Pick[]>(['entryPicks', vars.entryId])
      const optimisticPick: Pick = { id: -Date.now(), week: (previous?.length || 0) + 1, team_id: vars.teamId }
      queryClient.setQueryData(['entryPicks', vars.entryId], (old: Pick[] | undefined) => {
        return [...(old || []), optimisticPick]
      })
      return { previous }
    },
    onError: (err, vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['entryPicks', vars.entryId], context.previous)
      }
    },
    onSettled: (_data, _err, vars) => {
      queryClient.invalidateQueries({ queryKey: ['entryPicks', vars.entryId] })
      setModalOpen(false)
      setSelectedTeam(undefined)
    },
  })

  if (teamsQ.isLoading || picksQ.isLoading) return <div>Loading...</div>
  if (teamsQ.isError) return <div>Error loading teams</div>
  if (picksQ.isError) return <div>Error loading picks</div>

  const teams: TeamType[] = teamsQ.data || []
  const picks: Pick[] = picksQ.data || []

  const usedTeamIds = new Set(picks.map((p) => p.team_id))

  function handleSelect(team: TeamType) {
    setSelectedTeam(team)
    setModalOpen(true)
  }

  function handleConfirm() {
    if (!selectedTeam) return

    // call mutation to submit pick (optimistic update handled in mutation hooks)
    console.log('[Picks] handleConfirm mutate', { entryId: entryId || '', teamId: selectedTeam.id })
    submitPickMutation.mutate({ entryId: entryId || '', teamId: selectedTeam.id })
  }

  function handleCancel() {
    setModalOpen(false)
    setSelectedTeam(undefined)
  }

  return (
    <>
      <div>
        <h1>Pick Submission for Entry {entryId}</h1>
        <h2>Teams</h2>
        <TeamGrid teams={teams} usedTeamIds={usedTeamIds} onSelect={handleSelect} />

        <h2>Used Picks</h2>
        <ul data-testid="picks-list">
          {picks.map((p) => (
            <li key={p.id}>{`Week ${p.week}: Team ${p.team_id}`}</li>
          ))}
        </ul>
      </div>
      <ConfirmPickModal open={modalOpen} team={selectedTeam} onConfirm={handleConfirm} onCancel={handleCancel} />
    </>
  )
}
