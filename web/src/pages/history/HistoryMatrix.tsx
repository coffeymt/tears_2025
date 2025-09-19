import React, { useEffect, useMemo, useState } from 'react'

// Try to import FixedSizeGrid from react-window if available. If not, provide a fallback.
let FixedSizeGrid: any = null
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  FixedSizeGrid = require('react-window').FixedSizeGrid
} catch (err) {
  FixedSizeGrid = null
}

type MatrixResponse = {
  rows: string[] // row labels (e.g., entries)
  cols: string[] // column labels (e.g., weeks)
  cells: string[][] // cells[rowIdx][colIdx] = display value
}

function FallbackGrid({ data }: { data: MatrixResponse | null }) {
  if (!data) return <div>Loading matrix...</div>
  return (
    <div className="overflow-auto">
      <table className="min-w-full table-auto border-collapse">
        <thead>
          <tr>
            <th className="p-2 border">Entry / Week</th>
            {data.cols.map((c) => (
              <th key={c} className="p-2 border text-center">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r, ri) => (
            <tr key={r}>
              <td className="p-2 border">{r}</td>
              {data.cells[ri].map((cell, ci) => (
                <td key={ci} className="p-2 border text-center">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function HistoryMatrix() {
  const [data, setData] = useState<MatrixResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchMatrix() {
      try {
        const res = await fetch('/api/history/matrix')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json: MatrixResponse = await res.json()
        if (!cancelled) setData(json)
      } catch (err: any) {
        if (!cancelled) setError(err?.message || 'Failed to load matrix')
      }
    }
    fetchMatrix()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <div className="text-red-600">{error}</div>

  // If react-window is available, render a FixedSizeGrid
  if (FixedSizeGrid && data) {
    const rowCount = data.rows.length
    const columnCount = data.cols.length
    const rowHeight = 40
    const columnWidth = 120

    const Cell = ({ columnIndex, rowIndex, style }: any) => {
      const content = data.cells[rowIndex][columnIndex]
      return (
        <div className="border p-2 text-sm flex items-center justify-center" style={style}>
          {content}
        </div>
      )
    }

    return (
      <div>
        <div className="mb-2 text-sm text-gray-600">Virtualized matrix (react-window)</div>
        <div style={{ width: Math.min(columnCount * columnWidth + 150, 1200), height: 600 }}>
          <FixedSizeGrid
            columnCount={columnCount}
            columnWidth={columnWidth}
            height={600}
            rowCount={rowCount}
            rowHeight={rowHeight}
            width={Math.min(columnCount * columnWidth + 150, 1200)}
          >
            {Cell}
          </FixedSizeGrid>
        </div>
      </div>
    )
  }

  // else fallback
  return <FallbackGrid data={data} />
}
