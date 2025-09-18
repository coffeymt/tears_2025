import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import NewEntryModal from '../NewEntryModal'

describe('NewEntryModal', () => {
  it('renders and submits (happy path)', async () => {
    const onClose = vi.fn()
    const onCreated = vi.fn()
    render(<NewEntryModal isOpen={true} onClose={onClose} onCreated={onCreated} />)

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'New Title' } })

    const create = screen.getByRole('button', { name: /create/i })
    expect(create).toBeEnabled()

    // mock fetch to succeed
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1, title: 'New Title' }) })) as any

    fireEvent.click(create)

    await waitFor(() => expect(onCreated).toHaveBeenCalled())
    expect(onClose).toHaveBeenCalled()
  })
})
