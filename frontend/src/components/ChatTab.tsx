import { useEffect, useRef, useState } from 'react'
import { clearChatHistory, getChatHistory, postChat } from '../api'
import ChatInput from './ChatInput'
import ChatMessage, { Message } from './ChatMessage'
import SourceBadges from './SourceBadges'
import SuggestedQueries from './SuggestedQueries'

const GREETING: Message = {
  role: 'assistant',
  text:
    "Hi! I'm the SWS AI company assistant. Ask me anything about our HR policies, leave, benefits, resignation process, WFH guidelines, or any other company policy.",
  sources: [],
}

export default function ChatTab() {
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [pending, setPending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    getChatHistory()
      .then((rows) => {
        if (cancelled) return
        setMessages(rows.length > 0 ? [GREETING, ...rows] : [GREETING])
      })
      .catch(() => {
        // History unavailable (Supabase not configured, network error, etc.) —
        // start with just the greeting; the chat itself still works.
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, pending])

  const send = async (question: string) => {
    const q = question.trim()
    if (!q || pending) return
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', text: q, sources: [] }])
    setPending(true)
    try {
      const res = await postChat(q)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: res.answer, sources: res.sources },
      ])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setPending(false)
    }
  }

  const showSuggestions = messages.length === 1 && !pending && !loadingHistory
  const canClear = messages.length > 1 && !pending

  const clear = async () => {
    if (!canClear) return
    setError(null)
    setMessages([GREETING])
    try {
      await clearChatHistory()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <section className="chat-tab">
      <div className="info-banner">
        <span className="info-bot" aria-hidden>
          🤖
        </span>
        <span className="info-text">
          Powered by OpenAI + SWS AI company documents. Ask anything about company policies.
        </span>
        <button
          type="button"
          className="clear-chat-button"
          onClick={clear}
          disabled={!canClear}
          title="Clear saved chat history"
        >
          Clear chat
        </button>
      </div>

      <div className="messages">
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m}>
            {m.role === 'assistant' && m.sources.length > 0 && (
              <SourceBadges sources={m.sources} />
            )}
          </ChatMessage>
        ))}
        {pending && (
          <div className="message assistant">
            <div className="avatar" aria-hidden>
              🤖
            </div>
            <div className="bubble">
              <span className="typing">
                <span />
                <span />
                <span />
              </span>
            </div>
          </div>
        )}
        {error && <div className="error-banner">Error: {error}</div>}
        <div ref={bottomRef} />
      </div>

      {showSuggestions && <SuggestedQueries onPick={send} disabled={pending} />}

      <ChatInput pending={pending} onSend={send} />
    </section>
  )
}
