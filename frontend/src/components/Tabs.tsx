export type TabKey = 'upload' | 'chat'

interface Props {
  value: TabKey
  onChange: (next: TabKey) => void
}

export default function Tabs({ value, onChange }: Props) {
  return (
    <nav className="tabs">
      <button
        type="button"
        className={`tab ${value === 'upload' ? 'tab-active' : ''}`}
        onClick={() => onChange('upload')}
      >
        <span aria-hidden>⬆</span> Document Upload
      </button>
      <button
        type="button"
        className={`tab ${value === 'chat' ? 'tab-active' : ''}`}
        onClick={() => onChange('chat')}
      >
        <span aria-hidden>🤖</span> AI Assistant
      </button>
    </nav>
  )
}
