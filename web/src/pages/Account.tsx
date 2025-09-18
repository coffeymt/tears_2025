import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AccountProfileForm from '../components/AccountProfileForm';
import PasswordChangeForm from '../components/PasswordChangeForm';
import NotificationPreferences from '../components/NotificationPreferences';

async function fetchMe() {
  const res = await fetch('/api/auth/me');
  if (!res.ok) throw new Error('Failed to fetch user');
  return res.json();
}

export default function AccountPage(): JSX.Element {
  const qc = useQueryClient();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: fetchMe,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  if (isLoading) return <div>Loading account...</div>;
  if (isError) return <div>Error loading account: {(error as Error).message}</div>;

  const user = data;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">Account</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded p-4 max-w-md">
          <div className="mb-2">
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <div className="mt-1 text-gray-900">{user.email}</div>
          </div>
          <div className="mb-2">
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <div className="mt-1 text-gray-900">{user.name || '-'}</div>
          </div>
          <div className="mb-2">
            <label className="block text-sm font-medium text-gray-700">Mobile</label>
            <div className="mt-1 text-gray-900">{user.mobile || '-'}</div>
          </div>
        </div>

        <div className="bg-white shadow rounded p-4 max-w-md">
          <h2 className="text-lg font-medium mb-3">Edit Profile</h2>
          <AccountProfileForm
            defaultValues={{ name: user.name, mobile: user.mobile }}
            onSuccess={() => {
              // invalidate me to refetch updated profile
              qc.invalidateQueries({ queryKey: ['auth', 'me'] });
            }}
          />
          <div className="mt-6">
            <h2 className="text-lg font-medium mb-3">Notification Preferences</h2>
            <NotificationPreferences
              defaultValues={{ email: user.notifications?.email, sms: user.notifications?.sms }}
              onSuccess={() => qc.invalidateQueries({ queryKey: ['auth', 'me'] })}
            />
          </div>
          <div className="mt-6">
            <h2 className="text-lg font-medium mb-3">Change Password</h2>
            <PasswordChangeForm />
          </div>
        </div>
      </div>
    </div>
  );
}
