import React, { useEffect } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'

type Props = {
  value: string
  onChange: (html: string) => void
}

export default function BroadcastRichEditor({ value, onChange }: Props) {
  const editor = useEditor({
    extensions: [StarterKit, Link.configure({ openOnClick: true })],
    content: value || '',
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    }
  })

  // keep editor in sync when `value` changes externally
  useEffect(() => {
    if (!editor) return
    const current = editor.getHTML()
    if (value !== current) editor.commands.setContent(value || '')
  }, [value, editor])

  return (
    <div className="prose max-w-full border rounded p-2">
      <EditorContent editor={editor} />
    </div>
  )
}
