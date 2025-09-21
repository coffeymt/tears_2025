import React from 'react'
import DOMPurify from 'dompurify'

type Props = {
  subject: string
  bodyHtml: string
  onClose: () => void
}

export default function PreviewModal({ subject, bodyHtml, onClose }: Props) {
  const clean = DOMPurify.sanitize(bodyHtml || '')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black opacity-30" onClick={onClose} />
      <div className="relative bg-white rounded shadow-lg max-w-3xl w-full p-6 z-10">
        <h2 className="text-lg font-semibold">Preview</h2>
        <div className="mt-4">
          <h3 className="font-medium">{subject || '(no subject)'}</h3>
          <div className="mt-2 prose max-w-none" dangerouslySetInnerHTML={{ __html: clean }} />
        </div>
        <div className="mt-4 text-right">
          <button className="px-4 py-2 bg-gray-200 rounded" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
