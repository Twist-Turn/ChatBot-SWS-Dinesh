export default function Header() {
  return (
    <header className="header">
      <button className="back-button" type="button">
        ← Back
      </button>
      <div className="header-title">
        <div className="header-icon" aria-hidden>
          📄
        </div>
        <h1>SWS AI Document Hub</h1>
        <span className="live-badge">LIVE DEMO</span>
      </div>
      <button className="bell-button" type="button" aria-label="Notifications">
        🔔
      </button>
    </header>
  )
}
