import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import EntryItem from '../EntryItem'

const entry = { id: 1, title: 'Test Entry', created_at: new Date().toISOString() }

test('delete flow calls onDeleted on success', async () => {
  const onDeleted = vi.fn()
  render(<EntryItem entry={entry} onDeleted={onDeleted} />)

  const deleteBtn = screen.getByTestId('delete-1')
  fireEvent.click(deleteBtn)

  const confirmBtn = screen.getByTestId('confirm-delete-1')
  fireEvent.click(confirmBtn)

  await waitFor(() => {
    expect(onDeleted).toHaveBeenCalledWith(1)
  })
})

test('shows server error when delete fails', async () => {
  const onDeleted = vi.fn()
  // use entry id 999 which MSW handler treats as locked
  const locked = { ...entry, id: 999 }
  render(<EntryItem entry={locked} onDeleted={onDeleted} />)

  fireEvent.click(screen.getByTestId('delete-999'))
  fireEvent.click(screen.getByTestId('confirm-delete-999'))

  const err = await screen.findByTestId('entry-error-999')
  expect(err).toHaveTextContent('Cannot delete locked entry')
  expect(onDeleted).not.toHaveBeenCalled()
})
