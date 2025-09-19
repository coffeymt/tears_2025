/// <reference types="vitest" />
import React from 'react'
import { vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import UsersTable from './UsersTable'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '../../../components/ToastProvider'

const renderWithClient = (ui: React.ReactElement) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>
  )
}

const usersPage = (page = 1, search = '') => ({
  users: [
    { id: 1, email: `alice${search}@example.com`, is_admin: false, created_at: new Date().toISOString() },
    { id: 2, email: `bob${search}@example.com`, is_admin: true, created_at: new Date().toISOString() },
  ],
  page,
  pageSize: 10,
  total: 2,
})

describe('UsersTable', () => {
  beforeEach(() => {
    // simple fetch mock
    global.fetch = vi.fn((input: RequestInfo) => {
      const url = String(input)
      if (url.includes('/api/admin/users?page')) {
        return Promise.resolve(new Response(JSON.stringify(usersPage()), { status: 200 }))
      }
      if (url.match(/\/api\/admin\/users\/\d+$/) && (input as RequestInit).method === 'PATCH') {
        return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }))
      }
      if (url.match(/\/api\/admin\/users\/\d+\/password/) && (input as RequestInit).method === 'POST') {
        return Promise.resolve(new Response(null, { status: 200 }))
      }
      return Promise.resolve(new Response(null, { status: 404 }))
    }) as any
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders users and toggles admin', async () => {
    renderWithClient(<UsersTable />)
    expect(await screen.findByText(/alice/)).toBeInTheDocument()
    const checkbox = screen.getAllByRole('checkbox')[0]
    fireEvent.click(checkbox)
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/api\/admin\/users\/1/), expect.objectContaining({ method: 'PATCH' })))
  })

  it('opens confirm modal and posts reset password', async () => {
    renderWithClient(<UsersTable />)
    expect(await screen.findByText(/alice/)).toBeInTheDocument()
    const resetBtn = screen.getAllByText('Reset Password')[0]
    fireEvent.click(resetBtn)
    // modal shown
    expect(screen.getByText('Confirm Password Reset')).toBeInTheDocument()
    const confirm = screen.getByText('Confirm')
    fireEvent.click(confirm)
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringMatching(/\/api\/admin\/users\/1\/password/), expect.objectContaining({ method: 'POST' })))
  })
})
