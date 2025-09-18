import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useToast } from './Toast'

const PasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z.string().min(8, 'New password must be at least 8 characters'),
    confirm_password: z.string().min(1, 'Please confirm new password'),
  })
  .refine((v) => v.new_password === v.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

type PasswordFormValues = z.infer<typeof PasswordSchema>

export default function PasswordChangeForm() {
  const { register, handleSubmit, formState, reset } = useForm<PasswordFormValues>({
    resolver: zodResolver(PasswordSchema),
  })
  const toast = useToast()
  const [isSaving, setIsSaving] = useState(false)

  async function onSubmit(values: PasswordFormValues) {
    setIsSaving(true)
    try {
      const res = await fetch('/api/account/password', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        toast.push({ type: 'error', message: body?.message || 'Failed to change password' })
        setIsSaving(false)
        return
      }
      toast.push({ type: 'success', message: 'Password changed' })
      reset()
    } catch (err) {
      toast.push({ type: 'error', message: 'Network error' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="current-password" className="block text-sm font-medium text-gray-700">Current password</label>
        <input id="current-password" type="password" {...register('current_password')} className="mt-1 block w-full rounded border px-3 py-2" />
        {formState.errors.current_password && <p className="text-red-600 text-sm">{formState.errors.current_password.message}</p>}
      </div>

      <div>
        <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">New password</label>
        <input id="new-password" type="password" {...register('new_password')} className="mt-1 block w-full rounded border px-3 py-2" />
        {formState.errors.new_password && <p className="text-red-600 text-sm">{formState.errors.new_password.message}</p>}
      </div>

      <div>
        <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700">Confirm new password</label>
        <input id="confirm-password" type="password" {...register('confirm_password')} className="mt-1 block w-full rounded border px-3 py-2" />
        {formState.errors.confirm_password && <p className="text-red-600 text-sm">{formState.errors.confirm_password.message}</p>}
      </div>

      <div>
        <button type="submit" disabled={isSaving} className={`inline-flex items-center px-4 py-2 text-white rounded ${isSaving ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}>
          {isSaving ? 'Saving...' : 'Change password'}
        </button>
      </div>
    </form>
  )
}
