import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useToast } from './Toast'

const NotificationSchema = z.object({
  email: z.preprocess((v) => Boolean(v), z.boolean()),
  sms: z.preprocess((v) => Boolean(v), z.boolean()),
})

type NotificationValues = z.infer<typeof NotificationSchema>

export default function NotificationPreferences({
  defaultValues,
  onSuccess,
}: {
  defaultValues: Partial<NotificationValues>
  onSuccess?: (data: NotificationValues) => void
}) {
  const { register, handleSubmit, formState } = useForm<any>({
    resolver: zodResolver(NotificationSchema as any),
    defaultValues: {
      email: defaultValues.email ?? true,
      sms: defaultValues.sms ?? false,
    },
  })
  const toast = useToast()
  const [isSaving, setIsSaving] = useState(false)

  // no debug logs in production

  async function onSubmit(values: NotificationValues) {
    setIsSaving(true)
    try {
      // coerce values to booleans (form inputs may serialize differently in tests)
      const payload = { email: Boolean(values.email), sms: Boolean(values.sms) }
      const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : 'http://localhost'
      const url = new URL('/api/account/notifications', origin).toString()
      const res = await fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        let msg = 'Failed to save preferences'
        try {
          const err = await res.json()
          if (err?.message) msg = err.message
        } catch (e) {
          // ignore
        }
        toast.push({ type: 'error', message: msg })
        setIsSaving(false)
        return
      }
  const data = await res.json()
      toast.push({ type: 'success', message: 'Notification preferences saved' })
      onSuccess?.(data)
    } catch (e) {
      toast.push({ type: 'error', message: 'Network error' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="flex items-center space-x-3">
        <input id="notif-email" type="checkbox" {...register('email')} />
        <label htmlFor="notif-email" className="text-sm">Email notifications</label>
      </div>
      <div className="flex items-center space-x-3">
        <input id="notif-sms" type="checkbox" {...register('sms')} />
        <label htmlFor="notif-sms" className="text-sm">SMS notifications</label>
      </div>

      <div>
        <button
          type="submit"
          disabled={isSaving}
          className={`inline-flex items-center px-4 py-2 text-white rounded ${isSaving ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
        >
          {isSaving ? 'Saving...' : 'Save preferences'}
        </button>
      </div>
    </form>
  )
}
