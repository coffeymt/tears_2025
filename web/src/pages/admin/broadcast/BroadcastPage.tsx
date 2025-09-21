import React from 'react'
import BroadcastForm from './BroadcastForm'

export default function BroadcastPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Admin Broadcast</h1>
      <div className="bg-white shadow rounded p-4">
        <BroadcastForm />
      </div>
    </div>
  )
}
