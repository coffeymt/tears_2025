import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

interface FromState {
  from?: { pathname?: string }
}

export default function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()

  function onLogin() {
    // stub: pretend login succeeded and redirect
    const state = location.state as unknown
    // typed guard
    const from = (state && typeof state === 'object' && 'from' in state && (state as FromState).from?.pathname) || '/'
    navigate(from, { replace: true })
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Login</h2>
      <p className="mt-2">This is a stub login page for developer flows.</p>
      <button onClick={onLogin} className="mt-4 btn">
        Mock Login
      </button>
    </div>
  )
}
