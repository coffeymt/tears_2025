import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'

export default function AdminRoute() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div>Loading...</div>
  if (!user) return <Navigate to="/auth/login" replace />
  if (user.role !== 'admin') return <Navigate to="/" replace />
  return <Outlet />
}
