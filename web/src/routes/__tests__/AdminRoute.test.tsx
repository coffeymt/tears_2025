import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import AdminRoute from '../AdminRoute'
import { AuthProvider, AuthProvider as _AuthProvider } from '../../auth/AuthProvider'

function renderWithAuth(ui: React.ReactElement, initialEntries = ['/admin']) {
  return render(
    <_AuthProvider>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </_AuthProvider>
  )
}

describe('AdminRoute', () => {
  it('redirects unauthenticated users to /auth/login', () => {
    renderWithAuth(
      <Routes>
        <Route element={<AdminRoute />}>
          <Route path="/admin" element={<div>Admin</div>} />
        </Route>
        <Route path="/auth/login" element={<div>Login Page</div>} />
      </Routes>
    )

    expect(screen.getByText(/Login Page/i)).toBeDefined()
  })
})
