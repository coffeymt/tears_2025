import React from 'react'
import { Outlet, Link } from 'react-router-dom'

export default function AdminLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-6 px-4">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Admin Console</h1>
          <nav className="space-x-4">
            <Link to="/" className="text-sm text-blue-600">Home</Link>
            <Link to="/admin" className="text-sm text-blue-600">Admin</Link>
          </nav>
        </header>
        <main className="mt-6 grid grid-cols-4 gap-6">
          <aside className="col-span-1 bg-white p-4 rounded shadow-sm">
            <ul className="space-y-2 text-sm">
              <li><Link to="/admin/weeks" className="text-blue-600">Weeks</Link></li>
              <li><Link to="/admin/users" className="text-blue-600">Users</Link></li>
              <li><Link to="/admin/entries" className="text-blue-600">Entries</Link></li>
              <li><Link to="/admin/import" className="text-blue-600">Import</Link></li>
              <li><Link to="/admin/broadcast" className="text-blue-600">Broadcast</Link></li>
            </ul>
          </aside>
          <section className="col-span-3">
            <div className="bg-white p-6 rounded shadow-sm">
              <Outlet />
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
