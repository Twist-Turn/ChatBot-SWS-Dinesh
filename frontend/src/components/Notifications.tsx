import { useEffect, useState } from 'react'
import { subscribeNotifications, type AppNotification } from '../notifications'

const TOAST_TIMEOUT_MS = 5000

export default function Notifications() {
  const [toasts, setToasts] = useState<AppNotification[]>([])

  useEffect(() => {
    return subscribeNotifications((n) => {
      const tabIsHidden = document.visibilityState === 'hidden'
      const canNotify =
        'Notification' in window && Notification.permission === 'granted'

      if (tabIsHidden && canNotify) {
        try {
          new Notification(n.title, { body: n.body, tag: `sws-${n.id}` })
        } catch {
          // Some browsers throw on construction in worker-less contexts; ignore.
        }
      }

      setToasts((prev) => [...prev, n])
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== n.id))
      }, TOAST_TIMEOUT_MS)
    })
  }, [])

  const dismiss = (id: number) =>
    setToasts((prev) => prev.filter((t) => t.id !== id))

  return (
    <div className="toasts" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.kind}`}>
          <div className="toast-content">
            <div className="toast-title">{t.title}</div>
            {t.body && <div className="toast-body">{t.body}</div>}
          </div>
          <button
            type="button"
            className="toast-close"
            onClick={() => dismiss(t.id)}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
