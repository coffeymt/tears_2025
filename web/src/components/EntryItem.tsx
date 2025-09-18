import React, { useState } from 'react'

type Entry = {
  id: number
  title: string
  created_at?: string
}

type Props = {
  entry: Entry
  onUpdated?: (entry: Entry) => void
  onDeleted?: (id: number) => void
}

export default function EntryItem({ entry, onUpdated, onDeleted }: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(entry.title)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const startEdit = () => {
    setTitle(entry.title)
    setError(null)
    setEditing(true)
  }

  const cancel = () => {
    setTitle(entry.title)
    setError(null)
    setEditing(false)
  }

  const save = async () => {
    if (!title.trim()) {
      setError('Title cannot be empty')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : ''
      const res = await fetch(`${origin}/api/entries/${entry.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message || `Server error ${res.status}`)
      }
      const data = await res.json()
      onUpdated?.(data)
      setEditing(false)
    } catch (err: any) {
      setError(err?.message ?? 'Unknown error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="py-2 border-b" data-testid={`entry-${entry.id}`}>
      {!editing ? (
        <div className="flex justify-between items-center">
          <div>
            <div className="font-medium">{entry.title}</div>
            {entry.created_at && <div className="text-sm text-gray-500">{new Date(entry.created_at).toLocaleString()}</div>}
          </div>
          <div className="flex items-center space-x-2">
            <button onClick={startEdit} className="px-2 py-1 text-sm border rounded" data-testid={`edit-${entry.id}`}>
              Edit
            </button>
            {!confirmingDelete ? (
              <button
                onClick={() => setConfirmingDelete(true)}
                className="px-2 py-1 text-sm border rounded text-red-600"
                data-testid={`delete-${entry.id}`}
                disabled={deleting}
              >
                Delete
              </button>
            ) : (
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setConfirmingDelete(false)}
                  className="px-2 py-1 text-sm border rounded"
                  data-testid={`cancel-delete-${entry.id}`}
                  disabled={deleting}
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    setDeleting(true)
                    setError(null)
                    try {
                      const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : ''
                      const res = await fetch(`${origin}/api/entries/${entry.id}`, { method: 'DELETE' })
                      if (!res.ok) {
                        const body = await res.json().catch(() => ({}))
                        throw new Error(body?.message || `Server error ${res.status}`)
                      }
                      // notify parent
                      onDeleted?.(entry.id)
                    } catch (err: any) {
                      setError(err?.message ?? 'Unknown error')
                      setConfirmingDelete(false)
                    } finally {
                      setDeleting(false)
                    }
                  }}
                  className="px-2 py-1 text-sm border rounded bg-red-600 text-white"
                  data-testid={`confirm-delete-${entry.id}`}
                  disabled={deleting}
                >
                  {deleting ? 'Deleting…' : 'Confirm'}
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            save()
          }}
        >
          <div className="flex items-center space-x-2">
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="border px-2 py-1 flex-1" />
            <button type="button" onClick={cancel} className="px-2 py-1 border rounded">Cancel</button>
            <button type="submit" disabled={saving} className="px-2 py-1 bg-blue-600 text-white rounded">
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
          {error && <div data-testid={`entry-error-${entry.id}`} className="text-red-600 mt-1">{error}</div>}
        </form>
      )}
      {error && !editing && <div data-testid={`entry-error-${entry.id}`} className="text-red-600 mt-1">{error}</div>}
    </div>
  )
}
