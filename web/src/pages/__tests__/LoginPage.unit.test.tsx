import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../../auth/AuthProvider'
import LoginPage from '../LoginPage'

describe('LoginPage validation', () => {
  it('shows validation errors for empty fields', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByText(/Invalid email|required/i)).toBeDefined()
  })

  it('rejects short passwords', async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'test@example.com' } })
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: '123' } })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByText(/at least 6 characters/i)).toBeDefined()
  })
})
