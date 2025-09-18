import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'

export default function ProtectedRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <div>Loading...</div>
  if (!user) return <Navigate to="/auth/login" state={{ from: location }} replace />
  return <Outlet />
}
