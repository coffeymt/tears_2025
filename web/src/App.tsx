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
import Entries from './pages/Entries'
import Picks from './pages/Picks'
import AdminRoute from './routes/AdminRoute'
import AdminLayout from './pages/admin/AdminLayout'
import AdminIndex from './pages/admin'
import HistoryPage from './pages/history/HistoryPage'
import UsersPage from './pages/admin/users/UsersPage'
import WeeksList from './pages/admin/weeks/WeeksList'
import WeekGamesPage from './pages/admin/weeks/games'
import BroadcastPage from './pages/admin/broadcast/BroadcastPage'

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
  <Route path="entries" element={<Entries />} />
  <Route path="entries/:entryId/picks" element={<Picks />} />
        <Route element={<AdminRoute />}>
          <Route path="admin" element={<AdminLayout />}>
            <Route index element={<AdminIndex />} />
            <Route path="weeks" element={<WeeksList />} />
            <Route path="weeks/:weekId/games" element={<WeekGamesPage />} />
            {/* /admin/users, /admin/entries, /admin/import, /admin/broadcast will be added here */}
            <Route path="/history" element={<HistoryPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="broadcast" element={<BroadcastPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  )
}
