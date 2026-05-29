interface Props {
  sources: string[]
}

export default function SourceBadges({ sources }: Props) {
  if (sources.length === 0) return null
  return (
    <div className="source-badges">
      <span className="source-label">Sources:</span>
      {sources.map((s) => (
        <span key={s} className="source-pill">
          {s}
        </span>
      ))}
    </div>
  )
}
