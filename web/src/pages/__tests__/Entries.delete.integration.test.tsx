import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Entries from '../Entries'

// MSW handlers are already registered in test setup

test('delete entry from entries list (happy path)', async () => {
  render(<Entries />)

  // wait for list
  await screen.findByTestId('entries-list')

  // ensure first entry exists
  const item = await screen.findByTestId('entry-1')
  expect(item).toBeInTheDocument()

  // click delete for id 1
  fireEvent.click(screen.getByTestId('delete-1'))
  fireEvent.click(screen.getByTestId('confirm-delete-1'))

  // after deletion, entry 1 should be removed; entries list should still exist
  await waitFor(() => {
    expect(screen.queryByTestId('entry-1')).toBeNull()
  })
})

test('delete shows server error on failure', async () => {
  render(<Entries />)

  await screen.findByTestId('entries-list')

  // use entry id 999 to trigger MSW locked response; we need to inject it into the list
  // workaround: directly render EntryItem for this test
  const { getByTestId, findByTestId } = render(
    <div>
      <Entries />
    </div>
  )

  // Instead, render EntryItem directly for locked case
  // dynamic import to avoid circular
  const { default: EntryItem } = await import('../../components/EntryItem')
  const locked = { id: 999, title: 'Locked Entry', created_at: new Date().toISOString() }
  const onDeleted = vi.fn()
  const { findByTestId: findError } = render(<EntryItem entry={locked} onDeleted={onDeleted} />)

  fireEvent.click(await findError('delete-999'))
  fireEvent.click(await findError('confirm-delete-999'))

  const err = await findError('entry-error-999')
  expect(err).toHaveTextContent('Cannot delete locked entry')
  expect(onDeleted).not.toHaveBeenCalled()
})
