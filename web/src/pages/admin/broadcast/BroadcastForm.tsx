import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import BroadcastRichEditor from '../../../components/BroadcastRichEditor'
import PreviewModal from '../../../components/PreviewModal'
import ConfirmModal from '../../../components/ConfirmModal'
import { useToast } from '../../../components/ToastProvider'

export default function BroadcastForm() {
  const [subject, setSubject] = useState('')
  const [recipientFilter, setRecipientFilter] = useState<'all'|'active'|'eliminated'>('all')
  const [body, setBody] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const toast = useToast()

  const sendBroadcast = async (payload: { subject: string; body: string; recipients: string }) => {
    const res = await fetch('/api/admin/broadcast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Failed to send')
    return (await res.json())
  }

  const sendMutation = useMutation({
    mutationFn: sendBroadcast,
    onSuccess: () => {
      toast.push('Broadcast sent')
      setShowConfirm(false)
      setSubject('')
      setBody('')
    },
    onError: () => {
      toast.push('Failed to send broadcast')
    },
  })

  return (
    <form className="space-y-4">
      <div>
        <label htmlFor="broadcast-subject" className="block text-sm font-medium text-gray-700">Subject</label>
        <input id="broadcast-subject" value={subject} onChange={e => setSubject(e.target.value)} className="mt-1 block w-full border rounded px-3 py-2" />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Recipients</label>
        <div className="mt-1 flex gap-4">
          <label className="flex items-center gap-2">
            <input type="radio" name="recipients" checked={recipientFilter==='all'} onChange={() => setRecipientFilter('all')} />
            <span className="text-sm">All users</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" name="recipients" checked={recipientFilter==='active'} onChange={() => setRecipientFilter('active')} />
            <span className="text-sm">Active players</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" name="recipients" checked={recipientFilter==='eliminated'} onChange={() => setRecipientFilter('eliminated')} />
            <span className="text-sm">Eliminated players</span>
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Message</label>
        <div className="mt-1">
          <BroadcastRichEditor value={body} onChange={setBody} />
        </div>
      </div>

      <div className="flex gap-2">
        <button type="button" onClick={() => setShowPreview(true)} className="px-4 py-2 bg-gray-200 rounded">Preview</button>
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={() => {
            if (!subject.trim()) {
              toast.push('Subject is required')
              return
            }
            setShowConfirm(true)
          }}
          disabled={sendMutation.status === 'pending'}
        >
          {sendMutation.status === 'pending' ? 'Sending…' : 'Send'}
        </button>
      </div>

      {showPreview && (
        <PreviewModal subject={subject} bodyHtml={body} onClose={() => setShowPreview(false)} />
      )}

      <ConfirmModal
        open={showConfirm}
        title="Send Broadcast"
        message={`Send broadcast to ${recipientFilter === 'all' ? 'all users' : recipientFilter === 'active' ? 'active players' : 'eliminated players'}?`}
        onCancel={() => setShowConfirm(false)}
        onConfirm={() => sendMutation.mutate({ subject, body, recipients: recipientFilter })}
      />
    </form>
  )
}
