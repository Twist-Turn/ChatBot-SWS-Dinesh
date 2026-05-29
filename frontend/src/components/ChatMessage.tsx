import { ReactNode } from 'react'

export interface Message {
  role: 'user' | 'assistant'
  text: string
  sources: string[]
}

interface Props {
  message: Message
  children?: ReactNode
}

export default function ChatMessage({ message, children }: Props) {
  return (
    <div className={`message ${message.role}`}>
      {message.role === 'assistant' && (
        <div className="avatar" aria-hidden>
          🤖
        </div>
      )}
      <div className="bubble">
        <div className="text">{message.text}</div>
        {children}
      </div>
    </div>
  )
}
