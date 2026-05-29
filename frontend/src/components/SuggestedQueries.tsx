const QUERIES = [
  'What is the annual leave policy?',
  'How many sick leave days do I get?',
  'What is the notice period for resignation?',
  'What are the WFH guidelines?',
  'What health insurance benefits do we have?',
  'How does the performance review work?',
  'What tools does SWS AI use for communication?',
  'What is the IT password policy?',
]

interface Props {
  onPick: (q: string) => void
  disabled?: boolean
}

export default function SuggestedQueries({ onPick, disabled }: Props) {
  return (
    <div className="suggested">
      <div className="suggested-label">Try asking:</div>
      <div className="suggested-chips">
        {QUERIES.map((q) => (
          <button
            key={q}
            type="button"
            className="chip"
            onClick={() => onPick(q)}
            disabled={disabled}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
