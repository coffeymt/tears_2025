import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Entries from '../Entries'
import { rest } from 'msw'
import { server } from '../../test/msw/server'

describe('Entries page integration', () => {
  beforeEach(() => {
    // Default handler for entries list
    server.use(
      rest.get('http://localhost/api/entries', (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json([
            { id: 1, title: 'First entry', created_at: new Date().toISOString() },
          ])
        )
      })
    )
  })

  it('shows entries list when API returns items', async () => {
    render(
      <MemoryRouter initialEntries={["/entries"]}>
        <Routes>
          <Route path="/entries" element={<Entries />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByTestId('entries-loading')).toBeInTheDocument()

    await waitFor(() => expect(screen.getByTestId('entries-list')).toBeInTheDocument())

    expect(screen.queryByTestId('entries-empty')).not.toBeInTheDocument()
  })
})
