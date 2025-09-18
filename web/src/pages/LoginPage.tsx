import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../auth/AuthProvider'
import AuthInput from '../auth/components/AuthInput'
import SubmitButton from '../auth/components/SubmitButton'
import FormError from '../auth/components/FormError'

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters')
})

type FormData = z.infer<typeof schema>

interface FromState {
  from?: { pathname?: string }
}

export default function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { loginWithCredentials, isLoading, user } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormData) {
    try {
      await loginWithCredentials(values.email, values.password)
      const state = location.state as unknown
      const from = (state && typeof state === 'object' && 'from' in state && (state as FromState).from?.pathname) || '/'
      navigate(from, { replace: true })
    } catch (err: any) {
      // API-level errors are surfaced via FormError
    }
  }

  if (user) {
    navigate('/', { replace: true })
    return null
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Login</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
        <AuthInput label="Email" id="email" register={register('email')} error={errors.email} />
        <AuthInput label="Password" id="password" type="password" register={register('password')} error={errors.password} />
        <FormError>{/* placeholder for API errors */}</FormError>
        <SubmitButton disabled={isLoading}>{isLoading ? 'Logging in...' : 'Log in'}</SubmitButton>
      </form>
    </div>
  )
}
