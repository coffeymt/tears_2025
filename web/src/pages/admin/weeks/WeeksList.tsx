import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import WeeksForm from './WeeksForm'

type Week = {
  id: number
  week_number: number
  lock_time: string | null
}

async function fetchWeeks(): Promise<Week[]> {
  const res = await fetch('/api/admin/weeks')
  if (!res.ok) throw new Error('Failed to fetch weeks')
  return res.json()
}

export default function WeeksList() {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const { data: weeks, isLoading, isError } = useQuery({ queryKey: ['admin','weeks'], queryFn: fetchWeeks })

  const handleAdd = () => {
    setEditing(null)
    setOpen(true)
  }

  const handleEdit = (id: number) => {
    setEditing(id)
    setOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this week? This is irreversible.')) return
    try {
      const res = await fetch(`/api/admin/weeks/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      // invalidate and refetch
      qc.invalidateQueries({ queryKey: ['admin','weeks'] })
    } catch (err:any) {
      alert('Delete failed: ' + (err?.message ?? err))
    }
  }

  const handleManageGames = (id: number) => {
    // navigate to /admin/weeks/:id/games — keep it simple for now
    window.location.href = `/admin/weeks/${id}/games`
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Weeks</h3>
        <button onClick={handleAdd} className="px-3 py-1 bg-blue-600 text-white rounded">Add New Week</button>
      </div>

      <p className="text-sm text-gray-600 mt-2">List of weeks and admin actions.</p>

      {isLoading && <p className="mt-4">Loading...</p>}
      {isError && <p className="mt-4 text-red-600">Failed to load weeks.</p>}

      {weeks && (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full table-auto border-collapse">
            <thead>
              <tr>
                <th className="text-left p-2">Week</th>
                <th className="text-left p-2">Lock Time</th>
                <th className="text-left p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {weeks.map((w) => (
                <tr key={w.id} className="border-t">
                  <td className="p-2">{w.week_number}</td>
                  <td className="p-2">{w.lock_time ? new Date(w.lock_time).toLocaleString() : '—'}</td>
                  <td className="p-2">
                    <button onClick={() => handleEdit(w.id)} className="mr-2 text-sm text-blue-600">Edit</button>
                    <button onClick={() => handleDelete(w.id)} className="mr-2 text-sm text-red-600">Delete</button>
                    <button onClick={() => handleManageGames(w.id)} className="text-sm text-gray-700">Manage Games</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {open && (
        <WeeksForm
          initial={
            editing
              ? (() => {
                  const found = weeks?.find((w) => w.id === editing)
                  if (!found) return undefined
                  return { id: found.id, week_number: found.week_number, lock_time: found.lock_time ?? undefined }
                })()
              : undefined
          }
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  )
}
