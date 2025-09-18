import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../auth/AuthProvider'
import AuthInput from '../auth/components/AuthInput'
import SubmitButton from '../auth/components/SubmitButton'
import FormError from '../auth/components/FormError'

const schema = z
  .object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().email('Invalid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    passwordConfirm: z.string().min(1)
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: 'Passwords do not match',
    path: ['passwordConfirm']
  })

type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register: authRegister, isLoading } = useAuth()

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormData) {
    try {
      await authRegister(values.email, values.password)
      navigate('/', { replace: true })
    } catch (err: any) {
      // show API errors via FormError (not implemented here)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Register</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
        <AuthInput label="Name" id="name" register={register('name')} error={errors.name} />
        <AuthInput label="Email" id="email" register={register('email')} error={errors.email} />
        <AuthInput label="Password" id="password" type="password" register={register('password')} error={errors.password} />
        <AuthInput label="Confirm Password" id="passwordConfirm" type="password" register={register('passwordConfirm')} error={errors.passwordConfirm} />
        <FormError />
        <SubmitButton disabled={isLoading}>{isLoading ? 'Registering...' : 'Register'}</SubmitButton>
      </form>
    </div>
  )
}
