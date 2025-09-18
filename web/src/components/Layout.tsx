import React from 'react'
import { Outlet } from 'react-router-dom'
import TopNav from './TopNav'
import Footer from './Footer'
import { ToastProvider } from './Toast'

export default function Layout() {
  return (
    <ToastProvider>
      <div className="min-h-screen flex flex-col">
        <TopNav />
        <main className="flex-1 container mx-auto p-4">
          <Outlet />
        </main>
        <Footer />
      </div>
    </ToastProvider>
  )
}
