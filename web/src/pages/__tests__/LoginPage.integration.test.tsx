import React from 'react'
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import api from '../../api'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../auth/AuthProvider'
import LoginPage from '../LoginPage'

const mock = new MockAdapter((api as any))

afterEach(() => {
  mock.reset()
  localStorage.clear()
})

describe('LoginPage integration', () => {
  it('logs in and navigates to home', async () => {
    mock.onPost('/api/auth/login').reply(200, { token: 'tok', refresh: 'ref', user: { id: '1', email: 'a@b.com' } })

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/auth/login']}>
          <Routes>
            <Route path="/auth/login" element={<LoginPage />} />
            <Route path="/" element={<div>HOME</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )

    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'pw' } })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => expect(localStorage.getItem('token')).toBe('tok'))
    await waitFor(() => expect(screen.getByText(/HOME/i)).toBeDefined())
  })
})
