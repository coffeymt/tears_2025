import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'

interface FromState {
  from?: { pathname?: string }
}

export default function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { loginWithCredentials, isLoading, user } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await loginWithCredentials(email, password)
      const state = location.state as unknown
      const from = (state && typeof state === 'object' && 'from' in state && (state as FromState).from?.pathname) || '/'
      navigate(from, { replace: true })
    } catch (err: any) {
      setError(err?.message || 'Login failed')
    }
  }

  // If user already logged in, redirect
  if (user) {
    navigate('/', { replace: true })
    return null
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Login</h2>
      <form onSubmit={onSubmit} className="mt-4">
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} className="input" />
        </label>
        <label className="block mt-2">
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" />
        </label>
        {error && <div className="text-red-600 mt-2">{error}</div>}
        <button type="submit" disabled={isLoading} className="mt-4 btn">
          {isLoading ? 'Logging in...' : 'Log in'}
        </button>
      </form>
    </div>
  )
}
