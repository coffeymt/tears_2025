import React from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import AuthInput from '../auth/components/AuthInput'
import SubmitButton from '../auth/components/SubmitButton'
import FormError from '../auth/components/FormError'

const schema = z.object({ email: z.string().email('Invalid email') })
type FormData = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormData) {
    try {
      // call API to send reset link (not implemented in test environment)
    } catch (err) {
      // handle API errors
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Forgot Password</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
        <AuthInput label="Email" id="email" register={register('email')} error={errors.email} />
        <FormError />
        <SubmitButton>Send reset link</SubmitButton>
      </form>
    </div>
  )
}
