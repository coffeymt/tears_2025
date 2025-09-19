import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import debounce from 'lodash/debounce'
import ConfirmModal from '../../../components/ConfirmModal'
import { useToast } from '../../../components/ToastProvider'

type User = {
  id: number
  email: string
  is_admin: boolean
  created_at: string
}

type UsersResponse = {
  users: User[]
  page: number
  pageSize: number
  total: number
}

const fetchUsers = async (page: number, search?: string): Promise<UsersResponse> => {
  const q = new URLSearchParams()
  q.set('page', String(page))
  if (search) q.set('search', search)
  const res = await fetch(`/api/admin/users?${q.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch users')
  return (await res.json()) as UsersResponse
}

const UsersTable: React.FC = () => {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const queryClient = useQueryClient()

  // debounce input to avoid flooding the server
  useEffect(() => {
    const handler = debounce((val: string) => setDebouncedSearch(val), 400)
    handler(search)
    return () => {
      handler.cancel()
    }
  }, [search])

  // reset to page 1 whenever the debounced search term changes
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const { data, isLoading, isError } = useQuery<UsersResponse, Error, UsersResponse, [string, number, string]>({
    queryKey: ['admin-users', page, debouncedSearch],
    queryFn: () => fetchUsers(page, debouncedSearch),
  })

  // mutation to toggle admin flag
  const toggleAdmin = async ({ userId, isAdmin }: { userId: number; isAdmin: boolean }) => {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_admin: isAdmin }),
    })
    if (!res.ok) throw new Error('Failed to update user')
    return (await res.json()) as User
  }

  const mutation = useMutation<User, Error, { userId: number; isAdmin: boolean }>({
    mutationFn: toggleAdmin,
    // optimistic update
    onMutate: async ({ userId, isAdmin }: { userId: number; isAdmin: boolean }) => {
      await queryClient.cancelQueries({ queryKey: ['admin-users'] })
      const previous = queryClient.getQueryData<UsersResponse>(['admin-users', page, debouncedSearch])
      if (previous) {
        const updated = {
          ...previous,
          users: previous.users.map((u) => (u.id === userId ? { ...u, is_admin: isAdmin } : u)),
        }
        queryClient.setQueryData(['admin-users', page, debouncedSearch], updated)
      }
      return { previous }
    },
    onError: (_err: Error, _vars: { userId: number; isAdmin: boolean }, context: any) => {
      if (context?.previous) {
        queryClient.setQueryData(['admin-users', page, debouncedSearch], context.previous)
      }
      toast.push('Failed to update user admin status')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })

  React.useEffect(() => {
    if (data) {
      const lastPage = Math.max(1, Math.ceil(data.total / data.pageSize))
      if (data.page < lastPage) {
        queryClient.prefetchQuery({ queryKey: ['admin-users', data.page + 1, debouncedSearch], queryFn: () => fetchUsers(data.page + 1, debouncedSearch) })
      }
    }
  }, [data, queryClient])

  const toast = useToast()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmTarget, setConfirmTarget] = useState<{ id: number; email: string } | null>(null)

  if (isLoading) return <div>Loading users...</div>
  if (isError) return <div>Error loading users.</div>

  return (
    <div>
      <div className="mb-3">
        <input
          aria-label="Search users by email"
          placeholder="Search by email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 border rounded w-full max-w-md"
        />
      </div>
      <table className="min-w-full table-auto border">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-4 py-2 text-left">Email</th>
            <th className="px-4 py-2">Admin</th>
            <th className="px-4 py-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {data?.users.map((u: User) => (
            <tr key={u.id} className="border-t">
              <td className="px-4 py-2">{u.email}</td>
              <td className="px-4 py-2 text-center">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    checked={u.is_admin}
                    onChange={() => mutation.mutate({ userId: u.id, isAdmin: !u.is_admin })}
                    className="mr-2"
                  />
                  <span>{u.is_admin ? 'Yes' : 'No'}</span>
                </label>
              </td>
              <td className="px-4 py-2 text-right">
                <button
                  className="px-2 py-1 bg-red-100 text-red-700 rounded"
                  onClick={() => {
                    setConfirmTarget({ id: u.id, email: u.email })
                    setConfirmOpen(true)
                  }}
                >
                  Reset Password
                </button>
              </td>
              <td className="px-4 py-2">{new Date(u.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center justify-between mt-4">
        <button
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>

        <div>Page {data?.page} / {Math.max(1, Math.ceil((data?.total ?? 0) / (data?.pageSize ?? 1)))}</div>

        <button
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
          onClick={() => setPage((p) => p + 1)}
          disabled={data ? data.page >= Math.ceil(data.total / data.pageSize) : true}
        >
          Next
        </button>
      </div>
      <ConfirmModal
        open={confirmOpen}
        title="Confirm Password Reset"
        message={confirmTarget ? `Send password reset email to ${confirmTarget.email}?` : ''}
        onCancel={() => {
          setConfirmOpen(false)
          setConfirmTarget(null)
        }}
        onConfirm={async () => {
          if (!confirmTarget) return
          setConfirmOpen(false)
          const userId = confirmTarget.id
          setConfirmTarget(null)
          try {
            const res = await fetch(`/api/admin/users/${userId}/password`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed')
            toast.push('Password reset email sent')
          } catch (err) {
            toast.push('Failed to send password reset')
          }
        }}
      />
    </div>
  )
}

export default UsersTable
