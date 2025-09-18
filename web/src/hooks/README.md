useSiteTime hook
=================

Location: `web/src/hooks/useSiteTime.ts`

What it does
- Polls `GET /api/site-time` every 15s (configurable) and computes a client-server offset.
- Exposes `now: Date`, `offsetMs: number`, `isLoading`, and `error`.

Basic usage
-----------

```tsx
import useSiteTime from './useSiteTime'

function Component() {
  const { now, offsetMs, isLoading } = useSiteTime()
  return <div>{now.toISOString()} (offset: {offsetMs}ms)</div>
}
```

Testing
-------
- Tests live in `web/src/hooks/__tests__/useSiteTime.test.tsx` and use Vitest + Fake Timers.
- The tests mock the `fetch` global to return `server_time_ms` or `server_time`.
