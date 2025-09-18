import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import Entries from '../Entries'
import { rest } from 'msw'
import { server } from '../../test/msw/server'

describe('Entries rename flow', () => {
  it('renames an entry (happy path)', async () => {
    server.use(
      rest.get('*/api/entries', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json([{ id: 10, title: 'RenameMe', created_at: new Date().toISOString() }]))
      })
    )

    render(
      <MemoryRouter initialEntries={["/entries"]}>
        <Routes>
          <Route path="/entries" element={<Entries />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => screen.getByTestId('entry-10'))
    fireEvent.click(screen.getByTestId('edit-10'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Renamed' } })
    fireEvent.click(screen.getByText(/save/i))

    await waitFor(() => screen.getByText('Renamed'))
  })

  it('shows server validation error on bad title', async () => {
    // override PATCH to return 400
    server.use(
      rest.patch('*/api/entries/:id', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({ message: 'Title cannot be empty' }))
      }),
      rest.get('*/api/entries', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json([{ id: 11, title: 'BadRename', created_at: new Date().toISOString() }]))
      })
    )

    render(
      <MemoryRouter initialEntries={["/entries"]}>
        <Routes>
          <Route path="/entries" element={<Entries />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => screen.getByTestId('entry-11'))
    fireEvent.click(screen.getByTestId('edit-11'))
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.click(screen.getByText(/save/i))

    await waitFor(() => screen.getByTestId('entry-error-11'))
    expect(screen.getByTestId('entry-error-11')).toHaveTextContent(/title cannot be empty/i)
  })
})
