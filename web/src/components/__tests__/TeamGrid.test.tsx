import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import TeamGrid from '../TeamGrid'

const teams = [
  { id: 1, city: 'CityA', nickname: 'A' },
  { id: 2, city: 'CityB', nickname: 'B' },
  { id: 3, city: 'CityC', nickname: 'C' },
]

test('renders grid and disables used teams and calls onSelect for available', () => {
  const used = new Set<number>([2])
  const onSelect = vi.fn()
  render(<TeamGrid teams={teams} usedTeamIds={used} onSelect={onSelect} />)

  // all items present
  expect(screen.getByTestId('team-grid')).toBeInTheDocument()
  expect(screen.getByTestId('team-grid-item-1')).toBeInTheDocument()
  expect(screen.getByTestId('team-grid-item-2')).toBeInTheDocument()
  expect(screen.getByTestId('team-grid-item-3')).toBeInTheDocument()

  // used team shows 'Used' marker and is disabled
  expect(screen.getByTestId('team-grid-used-2')).toBeInTheDocument()
  expect((screen.getByTestId('team-grid-item-2') as HTMLButtonElement).disabled).toBe(true)

  // clicking available team should call onSelect
  fireEvent.click(screen.getByTestId('team-grid-item-1'))
  expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }))
})
