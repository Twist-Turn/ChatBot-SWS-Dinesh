export interface ChatResponse {
  answer: string
  sources: string[]
}

export interface DocumentEntry {
  source_file: string
  source_name: string
  chunks: number
}

export interface UploadResponse {
  filename: string
  source_name: string
  chunks_added: number
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export async function postChat(question: string): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  return handle<ChatResponse>(res)
}

const ADMIN_KEY_STORAGE = 'sws.adminKey'

export function getAdminKey(): string {
  return localStorage.getItem(ADMIN_KEY_STORAGE) ?? ''
}

export function setAdminKey(key: string): void {
  if (key) localStorage.setItem(ADMIN_KEY_STORAGE, key)
  else localStorage.removeItem(ADMIN_KEY_STORAGE)
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const headers: Record<string, string> = {}
  const adminKey = getAdminKey()
  if (adminKey) headers['X-Admin-Key'] = adminKey
  const res = await fetch('/api/upload', { method: 'POST', body: form, headers })
  return handle<UploadResponse>(res)
}

export async function getDocuments(): Promise<DocumentEntry[]> {
  const res = await fetch('/api/documents')
  const data = await handle<{ documents: DocumentEntry[] }>(res)
  return data.documents
}
