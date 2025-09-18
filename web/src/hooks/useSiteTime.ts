import { useEffect, useRef, useState } from 'react'

export type UseSiteTimeOptions = {
  /** Poll interval in milliseconds for refreshing server time (default 15000) */
  pollIntervalMs?: number
}

export type UseSiteTimeResult = {
  now: Date
  offsetMs: number
  isLoading: boolean
  error: Error | null
}

/**
 * useSiteTime
 * - Polls `GET /api/site-time` and computes a client-server offset.
 * - Exposes a continuously-updating `now` Date which is client clock + offset.
 */
export function useSiteTime(options?: UseSiteTimeOptions): UseSiteTimeResult {
  const pollIntervalMs = options?.pollIntervalMs ?? 15_000
  const [offsetMs, setOffsetMs] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  // tick triggers re-render each second
  const [, setTick] = useState<number>(0)
  const intervalRef = useRef<number | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    abortRef.current = new AbortController()

    async function fetchServerTime() {
      setIsLoading(true)
      setError(null)
      try {
        const start = Date.now()
        const res = await fetch('/api/site-time', { signal: abortRef.current?.signal })
        if (!res.ok) throw new Error(`status ${res.status}`)
        const json = await res.json()

        // Accept either `server_time` as ISO string or `server_time_ms` numeric
        const serverTimeMs = (() => {
          if (typeof json?.server_time_ms === 'number') return json.server_time_ms
          if (typeof json?.server_time === 'string') return Date.parse(json.server_time)
          return NaN
        })()

        const end = Date.now()
        if (Number.isNaN(serverTimeMs)) throw new Error('invalid server_time response')

        // estimate client time at server timestamp as midpoint between request start/end
        const approxClientAtServer = Math.round((start + end) / 2)
        const newOffset = serverTimeMs - approxClientAtServer
        setOffsetMs(newOffset)
      } catch (err: any) {
        if (err.name === 'AbortError') return
        setError(err instanceof Error ? err : new Error(String(err)))
      } finally {
        setIsLoading(false)
      }
    }

    // initial fetch
    fetchServerTime()

    // periodic refresh
    const refreshId = window.setInterval(() => {
      fetchServerTime()
    }, pollIntervalMs)
    intervalRef.current = refreshId

    // ticker to update now every second
    const tickId = window.setInterval(() => setTick((n) => n + 1), 1000)

    return () => {
      abortRef.current?.abort()
      if (intervalRef.current) window.clearInterval(intervalRef.current)
      if (tickId) window.clearInterval(tickId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollIntervalMs])

  const now = new Date(Date.now() + offsetMs)

  return { now, offsetMs, isLoading, error }
}

export default useSiteTime
