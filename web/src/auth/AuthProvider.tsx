import React, { createContext, useContext, useState, ReactNode } from 'react'

type User = { id: string; email: string; role?: string } | null

type AuthContextValue = {
  user: User
  isLoading: boolean
  login: (u: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null)
  const [isLoading] = useState(false)

  function login(u: User) {
    setUser(u)
  }

  function logout() {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
