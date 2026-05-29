import { FormEvent, useState } from 'react'

interface Props {
  pending: boolean
  onSend: (text: string) => void
}

export default function ChatInput({ pending, onSend }: Props) {
  const [text, setText] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const v = text.trim()
    if (!v || pending) return
    onSend(v)
    setText('')
  }

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Ask about policies, leave, benefits..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={pending}
        autoFocus
      />
      <button type="submit" disabled={pending || !text.trim()} aria-label="Send">
        ➤
      </button>
    </form>
  )
}
