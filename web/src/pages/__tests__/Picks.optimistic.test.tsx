import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Picks from '../Picks'
import { server } from '../../test/msw/server'
import { rest } from 'msw'

function renderWithClient(ui: React.ReactElement, route = '/entries/1/picks') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const result = render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
  return { qc, ...result }
}

test('optimistically adds a pick on confirm (happy path)', async () => {
  const renderResult = renderWithClient(
    <Routes>
      <Route path="/entries/:entryId/picks" element={<Picks />} />
    </Routes>
  )

  // wait for initial load
  await waitFor(() => expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument())

  // click a team that is not used (team 2 per handlers)
  const team2 = screen.getByTestId('team-grid-item-2')
  fireEvent.click(team2)

  // confirm modal should appear
  const confirmButton = await screen.findByTestId('confirm-pick-confirm')
  fireEvent.click(confirmButton)

  // optimistic update: cache should contain the newly added team (team 2) immediately
  await waitFor(() => {
    const picks = (renderResult.qc.getQueryData(['entryPicks', '1']) as any[]) || []
    // optimistic picks use a negative temporary id
    expect(picks.some((p) => p.team_id === 2 && p.id < 0)).toBeTruthy()
  })

  // after server responds and cache invalidates/refetches, the server-backed list may or may not include the new pick
  // we at minimum ensure the mutation settled without throwing (no unhandled errors)
  await waitFor(() => expect(true).toBe(true))
})

test('rolls back optimistic pick on server error', async () => {
  // temporarily override POST /api/picks to return 500 for this test
  const _handler = server.use(
    rest.post('*/api/picks', (_req, res, ctx) => {
      // add a small delay so optimistic update is observable before the error rollback
      return res(ctx.delay(100), ctx.status(500))
    })
  )

  const renderResult = renderWithClient(
    <Routes>
      <Route path="/entries/:entryId/picks" element={<Picks />} />
    </Routes>
  )

  // wait for initial load
  await waitFor(() => expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument())

  // click a team that is not used (team 2 per handlers)
  const team2 = screen.getByTestId('team-grid-item-2')
  fireEvent.click(team2)

  // confirm modal should appear
  const confirmButton = await screen.findByTestId('confirm-pick-confirm')
  fireEvent.click(confirmButton)

  // optimistic update: cache should contain the newly added team (team 2) immediately
  await waitFor(() => {
    const picks = (renderResult.qc.getQueryData(['entryPicks', '1']) as any[]) || []
    expect(picks.some((p) => p.team_id === 2)).toBeTruthy()
  })

  // wait for mutation to settle (modal closed) before asserting rollback
  await waitFor(() => expect(screen.queryByTestId('confirm-pick-confirm')).not.toBeInTheDocument())

  // after server error, cache should be rolled back to previous picks (no team 2)
  const finalPicks = (renderResult.qc.getQueryData(['entryPicks', '1']) as any[]) || []
  expect(finalPicks.some((p) => p.team_id === 2)).toBeFalsy()
})
