import React, { createContext, useContext, useState, useCallback } from 'react'

type Toast = { id: number; type: 'success' | 'error' | 'info'; message: string }

const ToastContext = createContext<{
  push: (t: Omit<Toast, 'id'>) => void
} | null>(null)

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    // Return a safe no-op implementation so components can call push() in tests
    return { push: (_: Omit<Toast, 'id'>) => {} }
  }
  return ctx
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = useCallback((t: Omit<Toast, 'id'>) => {
    setToasts((s) => [...s, { ...t, id: Date.now() }])
    // auto-dismiss
    setTimeout(() => {
      setToasts((s) => s.slice(1))
    }, 4000)
  }, [])

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div aria-live="polite" className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-2 rounded shadow text-white ${
              t.type === 'success' ? 'bg-green-600' : t.type === 'error' ? 'bg-red-600' : 'bg-gray-800'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
