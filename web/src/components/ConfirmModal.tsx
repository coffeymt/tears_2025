import React from 'react'

type ConfirmModalProps = {
  open: boolean
  title?: string
  message?: string
  onConfirm: () => void
  onCancel: () => void
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({ open, title = 'Confirm', message, onConfirm, onCancel }) => {
  if (!open) return null
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div className="bg-white rounded shadow p-4 w-full max-w-md">
        <h3 className="text-lg font-semibold">{title}</h3>
        {message && <p className="mt-2">{message}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button className="px-3 py-1" onClick={onCancel}>Cancel</button>
          <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmModal
