import { rest } from 'msw'

export const handlers = [
  // GET current user
  rest.get('/api/auth/me', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 1,
        email: 'user@example.com',
        name: 'Test User',
        mobile: '555-0100',
        notifications: { email: true, sms: false },
      })
    )
  }),

  // PATCH notification preferences
  rest.patch('/api/account/notifications', async (req, res, ctx) => {
  const body = await req.json()
    // basic validation
    if (typeof body.email !== 'boolean' || typeof body.sms !== 'boolean') {
      return res(ctx.status(400), ctx.json({ message: 'Invalid payload' }))
    }
    return res(ctx.status(200), ctx.json(body))
  }),

  // GET entries (wildcard origin so tests using different origins/ports match)
  rest.get('*/api/entries', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, title: 'First entry', created_at: new Date().toISOString() },
        { id: 2, title: 'Second entry', created_at: new Date().toISOString() },
      ])
    )
  }),

  // POST create entry
  rest.post('*/api/entries', async (req, res, ctx) => {
    const body = await req.json().catch(() => ({}))
    if (!body || typeof body.title !== 'string' || body.title.trim() === '') {
      return res(ctx.status(400), ctx.json({ message: 'Title is required' }))
    }
    return res(ctx.status(201), ctx.json({ id: Math.floor(Math.random() * 10000), title: body.title, created_at: new Date().toISOString() }))
  }),

  // PATCH update entry
  rest.patch('*/api/entries/:id', async (req, res, ctx) => {
    const { id } = req.params as { id: string }
    const body = await req.json().catch(() => ({}))
    if (!body || typeof body.title !== 'string' || body.title.trim() === '') {
      return res(ctx.status(400), ctx.json({ message: 'Title is required' }))
    }
    return res(ctx.status(200), ctx.json({ id: Number(id), title: body.title, created_at: new Date().toISOString() }))
  }),

  // DELETE entry
  rest.delete('*/api/entries/:id', async (req, res, ctx) => {
    const { id } = req.params as { id: string }
    // simulate a validation: id 999 -> cannot delete
    if (Number(id) === 999) {
      return res(ctx.status(400), ctx.json({ message: 'Cannot delete locked entry' }))
    }
    return res(ctx.status(204))
  }),

  // GET teams
  rest.get('*/api/teams', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: 1, city: 'New York', nickname: 'Giants' },
        { id: 2, city: 'Los Angeles', nickname: 'Rams' },
        { id: 3, city: 'Miami', nickname: 'Dolphins' },
      ])
    )
  }),
  
  // POST */api/picks - create pick
  rest.post('*/api/picks', async (req, res, ctx) => {
    const body = await req.json()
    const entryId = Number(body.entry_id)
    const teamId = Number(body.team_id)
    // naive created pick
    const created = { id: Math.floor(Math.random() * 100000) + 100, week: 1, team_id: teamId, entry_id: entryId }
    return res(ctx.status(201), ctx.json(created))
  }),
  
  // PATCH */api/picks/:id - update pick
  rest.patch('*/api/picks/:id', async (req, res, ctx) => {
    const { id } = req.params as { id: string }
    const body = await req.json()
    const updated = { id: Number(id), week: body.week ?? 1, team_id: body.team_id }
    return res(ctx.status(200), ctx.json(updated))
  }),

  // GET entry picks
  rest.get('*/api/entries/:entryId/picks', (req, res, ctx) => {
    const { entryId } = req.params as { entryId: string }
    // return sample picks for entry 1
    if (Number(entryId) === 1) {
      return res(
        ctx.status(200),
        ctx.json([
          { id: 11, week: 1, team_id: 1 },
          { id: 12, week: 2, team_id: 3 },
        ])
      )
    }
    return res(ctx.status(200), ctx.json([]))
  }),
]
