/// <reference types="vitest" />
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import BroadcastForm from '../BroadcastForm'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '../../../../components/ToastProvider'

const renderWithClient = (ui: React.ReactElement) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>
  )
}

// mock the rich editor to be a simple textarea
vi.mock('../../../../components/BroadcastRichEditor', () => ({
  default: function MockEditor({ value, onChange }: any) {
    return <textarea data-testid="mock-editor" value={value} onChange={(e) => onChange(e.target.value)} />
  }
}))

describe('Broadcast send flow', () => {
  afterEach(() => vi.restoreAllMocks())

  it('sends broadcast successfully (happy path)', async () => {
    // mock fetch to succeed
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ id: 1 }) })) as any

    renderWithClient(<BroadcastForm />)

    fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Hello' } })
    const editor = screen.getByTestId('mock-editor')
    fireEvent.change(editor, { target: { value: '<p>Hi</p>' } })

    // click send
    const send = screen.getByRole('button', { name: /Send/i })
    fireEvent.click(send)

    // confirm modal appears and confirm
    expect(await screen.findByRole('heading', { name: /Send Broadcast/i })).toBeInTheDocument()
    const confirmBtn = screen.getByText('Confirm')
    fireEvent.click(confirmBtn)

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/admin/broadcast', expect.anything()))
    expect(screen.getByText(/Broadcast sent/i)).toBeInTheDocument()
  })

  it('shows error toast when send fails', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false })) as any

    renderWithClient(<BroadcastForm />)

    fireEvent.change(screen.getByLabelText(/Subject/i), { target: { value: 'Hello' } })
    const editor = screen.getByTestId('mock-editor')
    fireEvent.change(editor, { target: { value: '<p>Hi</p>' } })

    const send = screen.getByRole('button', { name: /Send/i })
    fireEvent.click(send)

    // confirm modal
    expect(await screen.findByRole('heading', { name: /Send Broadcast/i })).toBeInTheDocument()
    fireEvent.click(screen.getByText('Confirm'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    expect(screen.getByText(/Failed to send broadcast/i)).toBeInTheDocument()
  })
})
