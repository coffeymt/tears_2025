import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react'
import api, { setTokenGetter, setRefreshTokenHandlers } from '../api'

type User = { id: string; email: string; role?: string } | null

type AuthContextValue = {
  user: User
  isLoading: boolean
  loginWithCredentials: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  getToken: () => string | null
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    // register token getter for api module to read from localStorage
    setTokenGetter(() => localStorage.getItem('token'))
    // wire refresh token handlers so api can call refresh endpoint
    setRefreshTokenHandlers((t: string | null) => {
      if (t) localStorage.setItem('refresh', t)
      else localStorage.removeItem('refresh')
    }, () => localStorage.getItem('refresh'))

    // attempt to load current user if token present
    const token = localStorage.getItem('token')
    if (token) {
      fetchCurrentUser()
    } else {
      setIsLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function fetchCurrentUser() {
    setIsLoading(true)
    try {
      const res = await api.get('/api/auth/me')
      setUser(res.data as User)
    } catch (err) {
      console.warn('fetchCurrentUser failed', err)
      setUser(null)
      localStorage.removeItem('token')
    } finally {
      setIsLoading(false)
    }
  }

  async function loginWithCredentials(email: string, password: string) {
    setIsLoading(true)
    try {
      const res = await api.post('/api/auth/login', { email, password })
      const { token, refresh, user: u } = res.data
      if (token) localStorage.setItem('token', token)
      if (refresh) localStorage.setItem('refresh', refresh)
      setUser(u as User)
    } finally {
      setIsLoading(false)
    }
  }

  async function register(email: string, password: string) {
    setIsLoading(true)
    try {
      const res = await api.post('/api/auth/register', { email, password })
      const { token, refresh, user: u } = res.data
      if (token) localStorage.setItem('token', token)
      if (refresh) localStorage.setItem('refresh', refresh)
      setUser(u as User)
    } finally {
      setIsLoading(false)
    }
  }

  function logout() {
    setUser(null)
    localStorage.removeItem('token')
  }

  function getToken() {
    return localStorage.getItem('token')
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, loginWithCredentials, register, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
