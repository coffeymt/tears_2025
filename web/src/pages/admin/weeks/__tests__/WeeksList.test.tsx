import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { server } from '../../../../test/msw/server'
import WeeksList from '../WeeksList'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('WeeksList admin CRUD', () => {
  const initialWeeks = [
    { id: 1, week_number: 1, lock_time: null },
    { id: 2, week_number: 2, lock_time: '2025-09-01T12:00' },
  ]

  let realFetch: typeof global.fetch

  let currentWeeks: Array<{ id: number; week_number: number; lock_time: string | null }>

  beforeEach(() => {
    realFetch = global.fetch
    currentWeeks = initialWeeks.map((w) => ({ ...w }))

    // stub global.fetch for GET/POST/PUT flows used by WeeksList
    global.fetch = vi.fn((input: RequestInfo, init?: RequestInit) => {
      const url = String(input)
      const method = init?.method ? String(init.method).toUpperCase() : 'GET'

      // GET list
      if (url.endsWith('/api/admin/weeks') && method === 'GET') {
        return Promise.resolve({ ok: true, json: async () => currentWeeks } as any)
      }

      // POST create
      if (url.endsWith('/api/admin/weeks') && method === 'POST') {
        return (async () => {
          const body = init?.body ? JSON.parse(String(init.body)) : {}
          const nextId = currentWeeks.reduce((m, c) => Math.max(m, c.id), 0) + 1
          const created = { id: nextId, week_number: body.week_number, lock_time: body.lock_time ?? null }
          currentWeeks = [...currentWeeks, created]
          return { ok: true, status: 201, json: async () => created } as any
        })()
      }

      // PUT update
      if (url.match(/\/api\/admin\/weeks\/\d+$/) && method === 'PUT') {
        const id = Number(url.split('/').pop())
        const body = init?.body ? JSON.parse(String(init.body)) : {}
        currentWeeks = currentWeeks.map((w) => (w.id === id ? { id, week_number: body.week_number, lock_time: body.lock_time ?? null } : w))
        const updated = currentWeeks.find((w) => w.id === id)!
        return Promise.resolve({ ok: true, status: 200, json: async () => updated } as any)
      }

      return Promise.resolve({ ok: false, status: 404 } as any)
    }) as any
  })

  afterEach(() => {
    global.fetch = realFetch
  })

  it('renders weeks and can add a new week', async () => {
    renderWithClient(<WeeksList />)

    // existing weeks should appear
    expect(await screen.findByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()

    // override POST handler to return created week
    server.use(
      rest.post('*/api/admin/weeks', async (req, res, ctx) => {
        const body = await req.json()
        return res(ctx.status(201), ctx.json({ id: 3, week_number: body.week_number, lock_time: body.lock_time ?? null }))
      }),
      // after create, return list including new week on subsequent GET
      rest.get('*/api/admin/weeks', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json([...initialWeeks, { id: 3, week_number: 3, lock_time: null }]))
      })
    )

    // open add modal
    fireEvent.click(screen.getByText('Add New Week'))

    // fill form
    const weekInput = screen.getByLabelText(/Week number/i)
    fireEvent.change(weekInput, { target: { value: '3' } })

    const saveBtn = screen.getByRole('button', { name: /save/i })
    fireEvent.click(saveBtn)

    // wait for the new week to appear in the table
    await waitFor(() => expect(screen.getByText('3')).toBeInTheDocument())
  })

  it('edits an existing week', async () => {
    renderWithClient(<WeeksList />)

    // wait for table to render
    expect(await screen.findByText('1')).toBeInTheDocument()

    // prepare server to accept PUT and then return updated list
    server.use(
      rest.put('*/api/admin/weeks/:id', async (req, res, ctx) => {
        const { id } = req.params as { id: string }
        const body = await req.json()
        return res(ctx.status(200), ctx.json({ id: Number(id), week_number: body.week_number, lock_time: body.lock_time ?? null }))
      }),
      rest.get('*/api/admin/weeks', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json([{ id: 1, week_number: 10, lock_time: null }, initialWeeks[1]]))
      })
    )

    // click Edit for week 1
    const editButtons = await screen.findAllByText('Edit')
    // assume first edit corresponds to week 1
    fireEvent.click(editButtons[0])

    // modal should show current value
    const weekInput = screen.getByLabelText(/Week number/i) as HTMLInputElement
    expect(weekInput.value).toBe('1')

    // change to 10
    fireEvent.change(weekInput, { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))

    // wait for updated value in table
    await waitFor(() => expect(screen.getByText('10')).toBeInTheDocument())
  })
})
