import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../auth/AuthProvider'
import RegisterPage from '../RegisterPage'
import ForgotPasswordPage from '../ForgotPasswordPage'
import ResetPasswordPage from '../ResetPasswordPage'

describe('Auth forms validation', () => {
  it('register shows errors when fields invalid', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      </AuthProvider>
    )

  fireEvent.click(screen.getByRole('button', { name: /register/i }))
  expect(await screen.findByText(/Name is required/i)).toBeDefined()
  expect(await screen.findByText(/Invalid email/i)).toBeDefined()
  })

  it('forgot password validates email', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <ForgotPasswordPage />
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'not-an-email' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    expect(await screen.findByText(/Invalid email/i)).toBeDefined()
  })

  it('reset password requires matching passwords', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/auth/reset-password?token=abc"]}>
          <ResetPasswordPage />
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/New Password/i), { target: { value: 'password1' } })
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password2' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))
    expect(await screen.findByText(/Passwords do not match/i)).toBeDefined()
  })
})
