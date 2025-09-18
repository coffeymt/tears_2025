import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import Dashboard from '../Dashboard'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// mock useAuth to return a current user for the Dashboard test
vi.mock('../../auth/AuthProvider', () => ({
  useAuth: () => ({ user: { id: '1', email: 'test@example.com' } }),
}))

function mockWeekAndEntries(weekData: any, entries: any[]) {
  ;(global as any).fetch = vi.fn((url: string) => {
    if (url.endsWith('/api/weeks/current')) {
      return Promise.resolve({ ok: true, json: async () => weekData })
    }
    if (/\/api\/users\/.+\/entries$/.test(url)) {
      return Promise.resolve({ ok: true, json: async () => entries })
    }
    return Promise.resolve({ ok: false })
  })
}

describe('Dashboard', () => {
  beforeEach(() => {
    // reset global fetch
    // @ts-ignore
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.resetAllMocks()
  })

  it('renders week and entries', async () => {
    const week = { week: 1, lock_time: new Date(Date.now() + 60000).toISOString() }
    const entries = [{ id: 1, name: 'Entry A', is_eliminated: false, is_paid: true }]
    mockWeekAndEntries(week, entries)

    const qc = new QueryClient()
    render(
      <QueryClientProvider client={qc}>
        <Dashboard />
      </QueryClientProvider>
    )

  await waitFor(() => expect(fetch).toHaveBeenCalled())

  expect(screen.getByText('Dashboard')).toBeInTheDocument()
  expect(screen.getByText('Your Entries')).toBeInTheDocument()
  // wait for entries to appear (React Query updates state async)
  await screen.findByText('Entry A')
  expect(screen.getByText('Entry A')).toBeInTheDocument()
  })
})
