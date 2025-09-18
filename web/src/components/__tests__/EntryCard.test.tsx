import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import EntryCard from '../EntryCard'

describe('EntryCard', () => {
  it('renders entry info and triggers make picks', () => {
    const entry = { id: 1, name: 'Team Alpha', is_eliminated: false, is_paid: true }
    const onMakePicks = vi.fn()
    render(<EntryCard entry={entry} onMakePicks={onMakePicks} />)

    expect(screen.getByText('Team Alpha')).toBeInTheDocument()
    expect(screen.getByText(/Active/)).toBeInTheDocument()
    expect(screen.getByText(/Paid/)).toBeInTheDocument()

    const btn = screen.getByTestId('entry-make-picks-1')
    fireEvent.click(btn)
    expect(onMakePicks).toHaveBeenCalledWith(1)
  })
})
