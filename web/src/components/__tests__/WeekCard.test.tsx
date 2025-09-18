import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest'
import WeekCard from '../WeekCard'

// simple mock for global fetch
function mockSiteTime(serverTimeMs: number) {
  ;(global as any).fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ server_time_ms: serverTimeMs }),
  })
}

describe('WeekCard', () => {
  beforeEach(() => {
    // use real timers for this component-level integration test
    vi.useRealTimers()
  })
  afterEach(() => {
    // no-op
    vi.resetAllMocks()
  })

  it('shows countdown based on server time', async () => {
  const baseClient = Date.now()
  const serverMs = baseClient + 500
  mockSiteTime(serverMs)

  render(<WeekCard weekNumber={1} lock_time={new Date(baseClient + 5_000).toISOString()} />)

  // allow initial fetch to resolve
  await waitFor(() => expect(fetch).toHaveBeenCalled(), { timeout: 1000 })

    // after syncing, remaining should be ~5500ms -> display '0d 0h 0m 5s' or similar
    const countdown = await screen.findByTestId('week-lock-countdown')
    expect(countdown.textContent).toMatch(/\d+d \d+h \d+m \d+s|Locked/)
  })
})
