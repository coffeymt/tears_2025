import React, { useState } from 'react'

type Props = {
  isOpen: boolean
  onClose: () => void
  onCreated?: (entry: { id: number; title: string; created_at?: string }) => void
}

export default function NewEntryModal({ isOpen, onClose, onCreated }: Props) {
  const [title, setTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : ''
      const res = await fetch(origin + '/api/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message || `Server error ${res.status}`)
      }
      const data = await res.json()
      setTitle('')
      onCreated?.(data)
      onClose()
    } catch (err: any) {
      setError(err?.message ?? 'Unknown error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 flex items-center justify-center bg-black/40">
      <div className="bg-white p-4 rounded w-96">
        <h2 className="text-lg font-bold mb-2">Create New Entry</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="block text-sm">Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full border px-2 py-1" />
          </div>
          {error && <div data-testid="new-entry-error" className="text-red-600 mb-2">{error}</div>}
          <div className="flex justify-end space-x-2">
            <button type="button" onClick={onClose} className="px-3 py-1 border rounded">Cancel</button>
            <button type="submit" disabled={saving || !title.trim()} className="px-3 py-1 bg-blue-600 text-white rounded">
              {saving ? 'Saving…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
