import React from 'react'

export default function SubmitButton({ children, disabled }: { children: React.ReactNode; disabled?: boolean }) {
  return (
    <button type="submit" disabled={disabled} className="btn mt-2" aria-disabled={disabled}>
      {disabled ? 'Please wait...' : children}
    </button>
  )
}
