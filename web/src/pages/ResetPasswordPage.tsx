import React from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import AuthInput from '../auth/components/AuthInput'
import SubmitButton from '../auth/components/SubmitButton'
import FormError from '../auth/components/FormError'

const schema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    passwordConfirm: z.string().min(1)
  })
  .refine((d) => d.password === d.passwordConfirm, { message: 'Passwords do not match', path: ['passwordConfirm'] })

type FormData = z.infer<typeof schema>

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormData) {
    if (!token) return
    try {
      // call API to reset password with token
      navigate('/auth/login')
    } catch (err) {
      // show API errors
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold">Reset Password</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
        <AuthInput label="New Password" id="password" type="password" register={register('password')} error={errors.password} />
        <AuthInput label="Confirm Password" id="passwordConfirm" type="password" register={register('passwordConfirm')} error={errors.passwordConfirm} />
        <FormError />
        <SubmitButton>Reset password</SubmitButton>
      </form>
    </div>
  )
}
