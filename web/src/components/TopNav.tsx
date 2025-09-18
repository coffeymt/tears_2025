import React, { useState } from 'react'
import { Link } from 'react-router-dom'

export default function TopNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="bg-white shadow">
      <div className="container mx-auto p-4 flex items-center justify-between">
        <Link to="/" className="text-lg font-bold">SBCCTears</Link>

        <button
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((s) => !s)}
          className="md:hidden p-2 rounded hover:bg-gray-100"
        >
          ☰
        </button>

        <nav className={`hidden md:flex items-center ${open ? 'block' : ''}`} aria-label="Main navigation">
          <Link to="/" className="mr-4">Home</Link>
          <Link to="/entries" className="mr-4">Entries</Link>
          <Link to="/account" className="mr-4">Account</Link>
          <Link to="/auth/login">Login</Link>
        </nav>
      </div>
    </header>
  )
}
