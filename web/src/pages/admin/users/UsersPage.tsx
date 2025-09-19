import React from 'react'
import UsersTable from './UsersTable'

const UsersPage: React.FC = () => {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-semibold mb-4">User Management</h1>
      <UsersTable />
    </div>
  )
}

export default UsersPage
