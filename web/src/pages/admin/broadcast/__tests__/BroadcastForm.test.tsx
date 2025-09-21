/// <reference types="vitest" />
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '../../../../components/ToastProvider'

// Mock the Tiptap wrapper to a simple textarea for tests using Vitest
// Correct relative path to reach `web/src/components/BroadcastRichEditor`
vi.mock('../../../../components/BroadcastRichEditor', () => ({
  default: function MockEditor({ value, onChange }: any) {
    return <textarea data-testid="mock-editor" value={value} onChange={(e) => onChange(e.target.value)} />
  }
}))

import BroadcastForm from '../BroadcastForm'

const renderWithClient = (ui: React.ReactElement) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>
  )
}

describe('BroadcastForm preview', () => {
  it('opens preview modal and shows sanitized HTML', () => {
    renderWithClient(<BroadcastForm />)

    // type subject
    const subject = screen.getByLabelText(/Subject/i)
    fireEvent.change(subject, { target: { value: 'Hello' } })

    // type into mocked editor
    const editor = screen.getByTestId('mock-editor')
    // include a script tag to ensure sanitization removes it
    fireEvent.change(editor, { target: { value: '<p>Hi <strong>there</strong></p><script>alert(1)</script>' } })

    // click preview
    const previewButton = screen.getByRole('button', { name: /Preview/i })
    fireEvent.click(previewButton)

  // modal should show subject and the sanitized content (script removed)
  // use heading role to avoid matching the Preview button
  expect(screen.getByRole('heading', { name: /Preview/i })).toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi')).toBeInTheDocument()
    expect(screen.queryByText('alert(1)')).not.toBeInTheDocument()
  })
})
