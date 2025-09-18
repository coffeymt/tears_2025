import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AccountPage from './pages/Account'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="auth/login" element={<LoginPage />} />
  <Route path="auth/register" element={<RegisterPage />} />
  <Route path="auth/forgot-password" element={<ForgotPasswordPage />} />
  <Route path="auth/reset-password" element={<ResetPasswordPage />} />
  <Route path="dashboard" element={<Dashboard />} />
  <Route path="account" element={<AccountPage />} />
        {/* protected and admin routes will be added in later subtasks */}
      </Route>
    </Routes>
  )
}
