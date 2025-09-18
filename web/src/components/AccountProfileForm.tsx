import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useToast } from './Toast';

const ProfileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  mobile: z.string().optional(),
});

type ProfileFormValues = z.infer<typeof ProfileSchema>;

export default function AccountProfileForm({
  defaultValues,
  onSuccess,
}: {
  defaultValues: Partial<ProfileFormValues>;
  onSuccess?: (data: ProfileFormValues) => void;
}) {
  const { register, handleSubmit, formState, setError } = useForm<ProfileFormValues>({
    resolver: zodResolver(ProfileSchema),
    defaultValues: {
      name: defaultValues.name || '',
      mobile: defaultValues.mobile || '',
    },
  });
  const toast = useToast();
  const [isSaving, setIsSaving] = useState(false);

  async function onSubmit(values: ProfileFormValues) {
    setIsSaving(true);
    const res = await fetch('/api/account', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    if (!res.ok) {
      let msg = 'Failed to update profile'
      try {
        const err = await res.json();
        if (err?.errors) {
          // assume zod-like errors: { field: message }
          Object.keys(err.errors).forEach((k) => {
            setError(k as any, { type: 'server', message: err.errors[k] });
          });
        }
        if (err?.message) msg = err.message
      } catch (e) {
        // ignore
      }
      toast.push({ type: 'error', message: msg });
      setIsSaving(false);
      return;
    }
    const data = await res.json();
    toast.push({ type: 'success', message: 'Profile updated' });
    setIsSaving(false);
    onSuccess?.(data);
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="account-name" className="block text-sm font-medium text-gray-700">Name</label>
        <input
          id="account-name"
          {...register('name')}
          className="mt-1 block w-full rounded border px-3 py-2"
        />
        {formState.errors.name && (
          <p className="text-red-600 text-sm">{formState.errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="account-mobile" className="block text-sm font-medium text-gray-700">Mobile</label>
        <input
          id="account-mobile"
          {...register('mobile')}
          className="mt-1 block w-full rounded border px-3 py-2"
        />
        {formState.errors.mobile && (
          <p className="text-red-600 text-sm">{formState.errors.mobile.message}</p>
        )}
      </div>

      <div>
        <button
          type="submit"
          disabled={isSaving}
          className={`inline-flex items-center px-4 py-2 text-white rounded ${isSaving ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  );
}
