import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Picks from '../Picks'

function renderWithClient(ui: React.ReactElement, route = '/entries/1/picks') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

test('renders teams and marks used teams from picks', async () => {
  renderWithClient(
    <Routes>
      <Route path="/entries/:entryId/picks" element={<Picks />} />
    </Routes>
  )

  // loading state
  expect(screen.getByText(/Loading.../i)).toBeInTheDocument()

  // await teams and picks to appear
  await waitFor(() => expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument())

  // team grid should be rendered
  const grid = screen.getByTestId('team-grid')
  expect(grid).toBeInTheDocument()

  // team 1 and 3 should be marked used per MSW handler (TeamGrid uses team-grid-used-<id>)
  expect(screen.getByTestId('team-grid-used-1')).toBeInTheDocument()
  expect(screen.getByTestId('team-grid-used-3')).toBeInTheDocument()
  // team 2 should not be marked used
  expect(screen.queryByTestId('team-grid-used-2')).not.toBeInTheDocument()

  // picks list should show two picks
  const picksList = screen.getByTestId('picks-list')
  expect(picksList).toBeInTheDocument()
  expect(picksList.children.length).toBeGreaterThanOrEqual(2)
})
