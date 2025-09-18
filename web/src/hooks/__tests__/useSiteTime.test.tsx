import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest'

import useSiteTime from '../useSiteTime'
import { act } from 'react-dom/test-utils'

function HookHarness({ pollIntervalMs = 15000 }: { pollIntervalMs?: number }) {
  const { now, offsetMs, isLoading, error } = useSiteTime({ pollIntervalMs })
  return (
    <div>
      <div data-testid="now">{now.toISOString()}</div>
      <div data-testid="offset">{offsetMs}</div>
      <div data-testid="loading">{String(isLoading)}</div>
      <div data-testid="error">{error ? error.message : ''}</div>
    </div>
  )
}

describe('useSiteTime', () => {
  const realFetch = global.fetch

  beforeEach(() => {
    vi.useFakeTimers()
    // reset fetch mock
    // @ts-ignore
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
    // @ts-ignore
    global.fetch = realFetch
    vi.restoreAllMocks()
  })

  it('calculates offset from server_time_ms and updates now', async () => {
    const t0 = 1_691_000_000_000 // some fixed ms
    // mock Date.now to a stable baseline during test
    const realNow = Date.now
    // @ts-ignore
    global.Date.now = () => t0

    // server returns server_time_ms slightly ahead
    // first fetch resolves quickly
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ server_time_ms: t0 + 2000 }) })

    render(<HookHarness />)

    // allow effect to run (advance fake timers inside React act to avoid warnings)
    await act(async () => {
      await vi.runOnlyPendingTimersAsync()
    })

    const offset = Number(screen.getByTestId('offset').textContent)
    expect(Math.abs(offset - 2000)).toBeLessThan(50)

    // now should be client + offset
    const nowIso = screen.getByTestId('now').textContent || ''
    const nowMs = Date.parse(nowIso)
    expect(Math.abs(nowMs - (t0 + offset))).toBeLessThan(100)

    // restore Date.now
    // @ts-ignore
    global.Date.now = realNow
  })

  it('handles failed initial fetch gracefully', async () => {
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({ ok: false, status: 500 })
    render(<HookHarness />)

    await act(async () => {
      await vi.runOnlyPendingTimersAsync()
    })

    const loading = screen.getByTestId('loading').textContent
    const error = screen.getByTestId('error').textContent
    expect(loading).toBe('false')
    expect(error).toBeTruthy()
  })
})
