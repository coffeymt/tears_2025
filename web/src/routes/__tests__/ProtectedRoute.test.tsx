import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ProtectedRoute from '../ProtectedRoute'
import { AuthProvider } from '../../auth/AuthProvider'

function renderWithAuth(ui: React.ReactElement, initialEntries = ['/protected']) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </AuthProvider>
  )
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to /auth/login', () => {
    renderWithAuth(
      <Routes>
        <Route element={React.createElement(ProtectedRoute)}>
          <Route path="/protected" element={React.createElement('div', null, 'Protected')} />
        </Route>
        <Route path="/auth/login" element={React.createElement('div', null, 'Login Page')} />
      </Routes>
    )

    expect(screen.getByText(/Login Page/i)).toBeDefined()
  })
})
