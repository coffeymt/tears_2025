import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AccountPage from '../Account';
import { vi, describe, it, expect, beforeEach } from 'vitest';

function setupFetchMocks(getResponse: any, patchResponse: any) {
  let current = { ...getResponse };
  (global as any).fetch = vi.fn(async (input: any, init?: any) => {
    const url = typeof input === 'string' ? input : input?.url;
    const method = init?.method ?? undefined;
    if (url === '/api/auth/me' && method === undefined) {
      return { ok: true, json: async () => ({ ...current }) } as any;
    }
    if (url === '/api/account' && method === 'PATCH') {
      // simulate server update
      const bodyText = init?.body;
      try {
        const body = JSON.parse(bodyText);
        current = { ...current, ...body };
      } catch (e) {
        current = { ...current, ...patchResponse };
      }
      return { ok: true, json: async () => ({ ...current }) } as any;
    }
    return { ok: false } as any;
  });
}

describe('Account page', () => {
  beforeEach(() => {
    // clear any previous mocks
    vi.resetAllMocks();
    (global as any).fetch = undefined;
  });

  it('renders user info and updates profile', async () => {
    const user = { email: 'test@example.com', name: 'Old Name', mobile: '123' };
    const updated = { email: 'test@example.com', name: 'New Name', mobile: '456' };
    setupFetchMocks(user, updated);

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={qc}>
        <AccountPage />
      </QueryClientProvider>
    );

    expect(await screen.findByText('test@example.com')).toBeInTheDocument();

  // change name (use fireEvent to avoid user-event dependency)
  const nameInputElement = screen.getByLabelText(/Name/i) as HTMLInputElement;
  fireEvent.change(nameInputElement, { target: { value: 'New Name' } });

  // find the profile form via the name input and target the exact "Save" button inside it
  const profileForm = nameInputElement.closest('form') as HTMLElement;
  const saveButton = within(profileForm).getByRole('button', { name: /^save$/i });
  fireEvent.click(saveButton);

    // after save, the mock returns updated user; wait for new name to appear
    expect(await screen.findByText('New Name')).toBeInTheDocument();
  });
});
