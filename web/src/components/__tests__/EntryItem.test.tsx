import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EntryItem from '../EntryItem'

describe('EntryItem', () => {
  it('allows inline rename and calls onUpdated on success', async () => {
    const entry = { id: 123, title: 'Old Title', created_at: new Date().toISOString() }
    const onUpdated = vi.fn()
    render(<EntryItem entry={entry} onUpdated={onUpdated} />)

    fireEvent.click(screen.getByTestId('edit-123'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New Title' } })

    // mock successful PATCH
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 123, title: 'New Title' }) })) as any

    fireEvent.click(screen.getByText(/save/i))
    await waitFor(() => expect(onUpdated).toHaveBeenCalled())
  })
})
