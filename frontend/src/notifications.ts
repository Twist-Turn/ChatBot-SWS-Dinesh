export type NotificationKind = 'success' | 'error' | 'info'

export interface AppNotification {
  id: number
  kind: NotificationKind
  title: string
  body?: string
}

type Listener = (n: AppNotification) => void

const listeners = new Set<Listener>()
let nextId = 0

export function notify(kind: NotificationKind, title: string, body?: string): void {
  const n: AppNotification = { id: nextId++, kind, title, body }
  listeners.forEach((l) => l(n))
}

export function subscribeNotifications(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function requestBrowserPermission(): void {
  if ('Notification' in window && Notification.permission === 'default') {
    void Notification.requestPermission()
  }
}
