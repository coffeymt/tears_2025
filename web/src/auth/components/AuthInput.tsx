import React from 'react'
import { FieldError, UseFormRegisterReturn } from 'react-hook-form'

type Props = {
  label: string
  id?: string
  type?: string
  register?: UseFormRegisterReturn
  error?: FieldError | undefined
}

export default function AuthInput({ label, id, type = 'text', register, error }: Props) {
  return (
    <div className="mb-2">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <input id={id} type={type} {...(register || {})} className={`input mt-1 ${error ? 'border-red-500' : ''}`} />
      {error && <div className="text-red-600 text-sm mt-1">{error.message}</div>}
    </div>
  )
}
