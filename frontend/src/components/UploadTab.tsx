import { DragEvent, useEffect, useRef, useState } from 'react'
import {
  getAdminKey,
  getDocuments,
  setAdminKey,
  uploadPdf,
  type DocumentEntry,
} from '../api'
import { notify, requestBrowserPermission } from '../notifications'

type FileStatus =
  | { state: 'pending' }
  | { state: 'uploading' }
  | { state: 'success'; chunks: number; sourceName: string }
  | { state: 'error'; message: string }

interface FileItem {
  id: number
  file: File
  status: FileStatus
}

let nextId = 0

export default function UploadTab() {
  const [items, setItems] = useState<FileItem[]>([])
  const [documents, setDocuments] = useState<DocumentEntry[]>([])
  const [dragging, setDragging] = useState(false)
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [adminKey, setAdminKeyLocal] = useState<string>(getAdminKey())
  const [adminKeySaved, setAdminKeySaved] = useState<boolean>(!!getAdminKey())
  const inputRef = useRef<HTMLInputElement>(null)

  const persistAdminKey = () => {
    setAdminKey(adminKey.trim())
    setAdminKeySaved(!!adminKey.trim())
  }

  const refreshDocs = async () => {
    setLoadingDocs(true)
    try {
      setDocuments(await getDocuments())
    } catch {
      // best-effort; the placeholder below will still render
    } finally {
      setLoadingDocs(false)
    }
  }

  useEffect(() => {
    void refreshDocs()
  }, [])

  const updateItem = (id: number, status: FileStatus) => {
    setItems((prev) => prev.map((x) => (x.id === id ? { ...x, status } : x)))
  }

  const runQueue = async (queued: FileItem[]) => {
    for (const item of queued) {
      updateItem(item.id, { state: 'uploading' })
      try {
        const res = await uploadPdf(item.file)
        updateItem(item.id, {
          state: 'success',
          chunks: res.chunks_added,
          sourceName: res.source_name,
        })
        notify(
          'success',
          `${res.source_name} indexed`,
          `${res.chunks_added} chunks added from ${item.file.name}.`,
        )
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e)
        updateItem(item.id, { state: 'error', message })
        notify('error', `Failed to index ${item.file.name}`, message)
      }
    }
    await refreshDocs()
  }

  const enqueue = (files: FileList | File[]) => {
    const pdfs = Array.from(files).filter(
      (f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'),
    )
    if (pdfs.length === 0) return
    requestBrowserPermission()
    const queued: FileItem[] = pdfs.map((file) => ({
      id: nextId++,
      file,
      status: { state: 'pending' },
    }))
    setItems((prev) => [...prev, ...queued])
    void runQueue(queued)
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer?.files?.length) enqueue(e.dataTransfer.files)
  }

  return (
    <section className="upload-tab">
      <div className="admin-key-row">
        <label htmlFor="admin-key" className="admin-key-label">
          🔒 Admin key
        </label>
        <input
          id="admin-key"
          type="password"
          placeholder="Required for uploads (set ADMIN_API_KEY in backend/.env)"
          value={adminKey}
          onChange={(e) => {
            setAdminKeyLocal(e.target.value)
            setAdminKeySaved(false)
          }}
          autoComplete="off"
        />
        <button type="button" onClick={persistAdminKey} disabled={!adminKey.trim()}>
          {adminKeySaved ? '✓ Saved' : 'Save'}
        </button>
      </div>

      <div
        className={`drop-zone ${dragging ? 'drop-zone-active' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
        }}
        role="button"
        tabIndex={0}
      >
        <div className="drop-icon" aria-hidden>
          ⬆
        </div>
        <div className="drop-title">Drag and drop PDFs here</div>
        <div className="drop-subtitle">or click to browse — PDF files only</div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) enqueue(e.target.files)
            e.target.value = ''
          }}
        />
      </div>

      {items.length > 0 && (
        <div className="upload-queue">
          <h3>Uploads</h3>
          <ul>
            {items.map((it) => (
              <li key={it.id} className={`upload-item upload-item-${it.status.state}`}>
                <span className="upload-name">{it.file.name}</span>
                <span className="upload-status">
                  {it.status.state === 'pending' && 'Queued'}
                  {it.status.state === 'uploading' && 'Indexing…'}
                  {it.status.state === 'success' &&
                    `✓ ${it.status.chunks} chunks added (${it.status.sourceName})`}
                  {it.status.state === 'error' && `✗ ${it.status.message}`}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="indexed-docs">
        <h3>
          Indexed Documents <span className="muted">({documents.length})</span>
        </h3>
        {loadingDocs && documents.length === 0 ? (
          <div className="muted">Loading…</div>
        ) : documents.length === 0 ? (
          <div className="muted">
            No documents indexed yet. Upload a PDF above, or run{' '}
            <code>python -m app.ingest</code> in the backend to load the 10 bundled policies.
          </div>
        ) : (
          <ul className="doc-list">
            {documents.map((d) => (
              <li key={d.source_file} className="doc-row">
                <span className="doc-icon" aria-hidden>
                  📄
                </span>
                <span className="doc-name">{d.source_name}</span>
                <span className="doc-meta">
                  {d.source_file} · {d.chunks} chunks
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
