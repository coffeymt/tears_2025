import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { act } from 'react'
import PasswordChangeForm from '../../components/PasswordChangeForm'

describe('PasswordChangeForm', () => {
  const realFetch = global.fetch

  beforeEach(() => {
    // @ts-ignore
    global.fetch = vi.fn()
  })
  afterEach(() => {
    // @ts-ignore
    global.fetch = realFetch
    vi.restoreAllMocks()
  })

  it('shows validation errors and submits successfully', async () => {
    render(<PasswordChangeForm />)

    // submit empty form (wrap in act for state updates)
    await act(async () => {
      fireEvent.click(screen.getByText('Change password'))
    })

    expect(await screen.findByText('Current password is required')).toBeInTheDocument()

    // fill form (use exact label matching to avoid ambiguity)
    await act(async () => {
      fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'oldpass' } })
      fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'newpassword' } })
      fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'newpassword' } })
    })

    // mock successful server response
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) })

    await act(async () => {
      fireEvent.click(screen.getByText('Change password'))
    })

    // success toast is rendered by ToastProvider in Layout in real app, but our hook is safe in tests
    // ensure fetch was called
    expect((global.fetch as any).mock.calls.length).toBeGreaterThan(0)
  })
})
