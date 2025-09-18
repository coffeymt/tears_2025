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
]
