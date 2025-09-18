import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import Entries from '../Entries'
import { rest } from 'msw'
import { server } from '../../test/msw/server'

describe('Entries create flow', () => {
  it('creates new entry and prepends to list (happy path)', async () => {
    // ensure initial entries
    server.use(
      rest.get('*/api/entries', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json([{ id: 1, title: 'Existing', created_at: new Date().toISOString() }]))
      })
    )

    render(
      <MemoryRouter initialEntries={["/entries"]}>
        <Routes>
          <Route path="/entries" element={<Entries />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => screen.getByTestId('entries-list'))

    // open modal
    fireEvent.click(screen.getByTestId('open-new-entry'))

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Created Title' } })

    // server handler for POST already exists in handlers.ts and returns 201
    fireEvent.click(screen.getByRole('button', { name: /create/i }))

    await waitFor(() => expect(screen.queryByTestId('entries-error')).not.toBeInTheDocument())

    // new item should be present
    await waitFor(() => screen.getByText('Created Title'))
  })

  it('shows error on server validation failure', async () => {
    // override POST to return 400
    server.use(
      rest.post('*/api/entries', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({ message: 'Title is required' }))
      })
    )

    render(
      <MemoryRouter initialEntries={["/entries"]}>
        <Routes>
          <Route path="/entries" element={<Entries />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => screen.getByTestId('entries-list'))
  fireEvent.click(screen.getByTestId('open-new-entry'))
  const input = screen.getByRole('textbox')
  // provide a non-empty title so the submit button is enabled; server will still return 400
  fireEvent.change(input, { target: { value: 'Invalid Title' } })
  fireEvent.click(screen.getByRole('button', { name: /create/i }))

  await waitFor(() => screen.getByTestId('new-entry-error'))
  expect(screen.getByTestId('new-entry-error')).toHaveTextContent(/title is required/i)
  })
})
