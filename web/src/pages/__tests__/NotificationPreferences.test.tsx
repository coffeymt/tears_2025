import React from 'react'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import NotificationPreferences from '../../components/NotificationPreferences'
import { ToastProvider } from '../../components/Toast'
import { describe, it, beforeEach, vi, expect } from 'vitest'
import { rest } from 'msw'
import { server } from '../../test/msw/server'

describe('NotificationPreferences', () => {
  beforeEach(() => {
    // ensure any previous mocks are cleared
    vi.restoreAllMocks()
  })

  it('submits preferences and shows success', async () => {
    const onSuccess = vi.fn()
    render(
      <ToastProvider>
        <NotificationPreferences defaultValues={{ email: true, sms: false }} onSuccess={onSuccess} />
      </ToastProvider>
    )

  // --

    const saveBtn = screen.getByRole('button', { name: /save preferences/i })
  const emailCheckbox = screen.getByLabelText(/Email notifications/i) as HTMLInputElement
  const smsCheckbox = screen.getByLabelText(/SMS notifications/i) as HTMLInputElement
  // explicitly set checkbox states using change to ensure RHF sees the values
  fireEvent.change(emailCheckbox, { target: { checked: true } })
  fireEvent.change(smsCheckbox, { target: { checked: false } })
    // click the save button to submit (keeps parity with the error-case test)
    await act(async () => {
      fireEvent.click(saveBtn)
    })
    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled()
    })
    // first call should include the saved preference shape
    const calledArg = (onSuccess as any).mock.calls[0][0]
    expect(calledArg).toEqual(expect.objectContaining({ email: true, sms: false }))
  })

  it('shows error toast when server returns 400', async () => {
    // override the handler to return 400
    server.use(
      rest.patch('/api/account/notifications', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({ message: 'Invalid payload' }))
      })
    )
    const onSuccess = vi.fn()
    render(
      <ToastProvider>
        <NotificationPreferences defaultValues={{ email: true, sms: false }} onSuccess={onSuccess} />
      </ToastProvider>
    )

    const saveBtn = screen.getByRole('button', { name: /save preferences/i })

    await act(async () => {
      fireEvent.click(saveBtn)
    })

    // onSuccess should not be called on error
    await waitFor(() => {
      expect(onSuccess).not.toHaveBeenCalled()
    })

    // toast visible with server message
    await waitFor(() => expect(screen.getByText(/invalid payload/i)).toBeInTheDocument())
  })

  it('shows error toast when server returns 500', async () => {
    server.use(
      rest.patch('/api/account/notifications', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'Server error' }))
      })
    )

    const onSuccess = vi.fn()
    render(
      <ToastProvider>
        <NotificationPreferences defaultValues={{ email: true, sms: false }} onSuccess={onSuccess} />
      </ToastProvider>
    )

    const saveBtn = screen.getByRole('button', { name: /save preferences/i })

    await act(async () => {
      fireEvent.click(saveBtn)
    })

    await waitFor(() => {
      expect(onSuccess).not.toHaveBeenCalled()
    })

    await waitFor(() => expect(screen.getByText(/server error/i)).toBeInTheDocument())
  })

  it('shows network error toast on fetch/network failure', async () => {
    server.use(
      rest.patch('/api/account/notifications', (req, res) => {
        // simulate network failure
        return res.networkError('Failed to connect')
      })
    )

    const onSuccess = vi.fn()
    render(
      <ToastProvider>
        <NotificationPreferences defaultValues={{ email: true, sms: false }} onSuccess={onSuccess} />
      </ToastProvider>
    )

  // --

    const saveBtn = screen.getByRole('button', { name: /save preferences/i })

    await act(async () => {
      fireEvent.click(saveBtn)
    })

    await waitFor(() => expect(onSuccess).not.toHaveBeenCalled())
    await waitFor(() => expect(screen.getByText(/network error/i)).toBeInTheDocument())
  })

  it('disables submit button while saving', async () => {
    // handler that delays response so we can check disabled state during request
    server.use(
      rest.patch('/api/account/notifications', (req, res, ctx) => {
        return res(ctx.delay(200), ctx.status(200), ctx.json({ email: true, sms: false }))
      })
    )

    const onSuccess = vi.fn()
    render(
      <ToastProvider>
        <NotificationPreferences defaultValues={{ email: true, sms: false }} onSuccess={onSuccess} />
      </ToastProvider>
    )

    const saveBtn = screen.getByRole('button', { name: /save preferences/i })

    // click and immediately check disabled state
    await act(async () => {
      fireEvent.click(saveBtn)
    })

    // button should show saving and be disabled
    expect(saveBtn).toBeDisabled()
    expect(saveBtn).toHaveTextContent(/saving/i)

    // after request completes, button re-enabled
    await waitFor(() => expect(saveBtn).not.toBeDisabled())
    await waitFor(() => expect(onSuccess).toHaveBeenCalled())
  })
})
