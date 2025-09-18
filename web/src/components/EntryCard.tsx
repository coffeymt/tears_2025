import React from 'react'

export type Entry = {
  id: number
  name: string
  is_eliminated: boolean
  is_paid: boolean
}

type Props = {
  entry: Entry
  onMakePicks?: (entryId: number) => void
}

export default function EntryCard({ entry, onMakePicks }: Props) {
  return (
    <div data-testid={`entry-card-${entry.id}`} className="p-3 border rounded bg-white flex items-center justify-between">
      <div>
        <div className="font-semibold">{entry.name}</div>
        <div className="text-sm text-gray-500">
          {entry.is_eliminated ? 'Eliminated' : 'Active'} • {entry.is_paid ? 'Paid' : 'Unpaid'}
        </div>
      </div>
      <div>
        <button
          data-testid={`entry-make-picks-${entry.id}`}
          onClick={() => onMakePicks?.(entry.id)}
          className="px-3 py-1 bg-blue-600 text-white rounded"
        >
          Make Picks
        </button>
      </div>
    </div>
  )
}
