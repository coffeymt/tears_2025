import React from 'react'

export default function FormError({ children }: { children?: React.ReactNode }) {
  if (!children) return null
  return <div className="text-red-600 mt-2">{children}</div>
}
