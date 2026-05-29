# SWS AI Document Hub — RAG Chatbot

A Retrieval-Augmented-Generation (RAG) chatbot over SWS AI's internal policy PDFs. Employees can ask natural-language questions ("How many sick leaves do I get?", "What's the notice period for resignation?") and receive grounded answers sourced directly from the company documents — no hallucination, with the source documents shown for every answer.

Built for the SWS AI Engineer take-home assessment.

---

## Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │  Backend (Python · FastAPI · uvicorn)                       │
                 │                                                            │
PDFs ──► ingest ─┼─► pypdf ──► RecursiveCharacterTextSplitter(500/50) ──┐    │
(Documents/)     │                                                       ▼    │
                 │                              OpenAI text-embedding-3-small  │
                 │                                            │                │
                 │                                            ▼                │
                 │                              ChromaDB (persistent, on disk) │
                 │                                            ▲                │
                 │                                            │ top-5 cosine   │
                 │  POST /api/chat ──► embed q ──► retrieve ──┘                │
                 │                                            │                │
                 │                       grounded context ────┘                │
                 │                                │                            │
                 │                                ▼                            │
                 │                       OpenAI gpt-4o-mini ──► {answer, ...}  │
                 │                                                             │
                 │  POST /api/upload   multipart PDF → indexer.index_pdf       │
                 │  GET  /api/documents  list of indexed source docs           │
                 └────────────────────────────────────────────────────────────┘
                          ▲                              ▲
                          │ /api/* via Vite proxy        │
                          │                              │
                 ┌────────┴──────────────────────────────┴─────────────────────┐
                 │  Frontend (React 19 · Vite · TypeScript · Livvic)           │
                 │                                                             │
                 │   ┌─ Document Upload tab ────────────────────────────┐      │
                 │   │  drag-drop / file-picker → uploads → index list  │      │
                 │   └──────────────────────────────────────────────────┘      │
                 │                                                             │
                 │   ┌─ AI Assistant tab ───────────────────────────────┐      │
                 │   │  chat thread · suggested chips · source pills    │      │
                 │   └──────────────────────────────────────────────────┘      │
                 └─────────────────────────────────────────────────────────────┘
```

### Architecture decisions

| Decision | Choice | Why |
|---|---|---|
| Backend | **FastAPI** + uvicorn | Async, typed, auto OpenAPI at `/docs`, easy CORS for the React dev server. |
| Frontend | **React 19** + Vite + TypeScript | Fast dev loop, `vite dev` proxies `/api/*` to FastAPI so no CORS hassles. |
| PDF parsing | **`pypdf`** | Lightweight, pure-Python, handles the text-only policy PDFs reliably and exposes page numbers for metadata. |
| Chunking | `RecursiveCharacterTextSplitter`, **chunk_size=500, overlap=50** | Brief's recommended values. Small chunks give precise retrieval for policy-style Q&A; 50-char overlap keeps sentences that straddle a chunk boundary intact. Separators `["\n\n", "\n", ". ", " ", ""]` prefer paragraph / sentence breaks before falling back to words. |
| Embeddings | OpenAI **`text-embedding-3-small`** (1536 dim) | Cheap (~$0.02 / 1M tokens), strong quality, easily the right choice when only an OpenAI key is available. Batched 64 chunks per request during ingest. |
| Vector DB | **ChromaDB** in local persistent mode (`backend/chroma_db/`) | Brief's recommended option. Zero external services to provision, persists to disk between FastAPI restarts, supports the metadata filtering we need to make uploads idempotent (`collection.delete(where={"source_file": filename})`). Cosine similarity (`"hnsw:space": "cosine"`). |
| Retrieval k | **top-5** | Balances recall and prompt size. Five 500-char chunks ≈ 2.5 KB of context — leaves plenty of room in `gpt-4o-mini`'s 128k window while covering questions that span multiple documents (e.g. leave + WFH). |
| Chat model | OpenAI **`gpt-4o-mini`** (`temperature=0.1`) | Cheap, fast, strong instruction-following — more than enough for grounded extraction from short policy chunks. Configurable via `OPENAI_CHAT_MODEL` env var if a stronger model is desired. |
| Grounding | System prompt instructs the model to answer only from context and to respond **verbatim** `"I don't have that information in the company documents."` when context is insufficient. The server short-circuits the `sources` array to `[]` whenever the response equals that fallback string, so the UI never shows a citation for a non-answer. |
| Source attribution | Friendly-name map (`SWS-AI-leave-policy.pdf` → "Leave Policy") with a title-case fallback for uploads. The top-5 chunks' source names are deduplicated and returned alongside every answer. |

---

## Project structure

```
SWSAI/
├── Documents/                   # 10 SWS AI policy PDFs (the bundled knowledge base)
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app: /api/chat, /api/upload, /api/documents, /health
│   │   ├── rag.py               # embed q -> retrieve -> grounded LLM call
│   │   ├── indexer.py           # shared PDF -> chunks -> embeddings -> Chroma pipeline
│   │   ├── ingest.py            # one-shot CLI: rebuild collection from Documents/
│   │   ├── sources.py           # filename -> friendly display name
│   │   ├── prompts.py           # grounded system prompt + user-message builder
│   │   └── config.py            # pydantic-settings env loader
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # tab state (upload | chat)
│   │   ├── api.ts               # fetch helpers
│   │   ├── styles.css           # Livvic + blue/white tokens
│   │   ├── main.tsx
│   │   └── components/          # Header, Tabs, ChatTab, UploadTab, etc.
│   ├── index.html               # Livvic 400/500/600/700 from Google Fonts
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts           # proxies /api -> http://localhost:8000
└── README.md
```

---

## Setup

### Prerequisites
- Python **3.10+** (tested on 3.14)
- Node **18+**
- An **OpenAI API key**

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste your key:
#   OPENAI_API_KEY=sk-...

# One-time: build the vector store from the 10 bundled PDFs
python -m app.ingest

# Run the API
uvicorn app.main:app --reload --port 8000
```

`http://localhost:8000/docs` exposes the interactive OpenAPI explorer.

### Frontend (in a separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The Vite dev server proxies `/api/*` to the backend automatically.

---

## Using the app

### AI Assistant tab
Type a question in the input field at the bottom, or click one of the suggested-query chips that appears on first load. The bot answers using only retrieved content from the indexed documents; the source documents used for each answer are shown as blue pill badges under the message. Out-of-scope questions return the exact fallback `"I don't have that information in the company documents."` and no source pills.

### Document Upload tab
Drop one or more PDFs onto the upload zone, or click to pick files. Each file is sent to `POST /api/upload`, parsed, chunked, embedded, and added to the same Chroma collection. The bottom panel lists every indexed PDF with its friendly name, filename, and chunk count. Re-uploading the same filename replaces its prior chunks (idempotent).

---

## API reference

| Method | Path | Body | Response |
|---|---|---|---|
| `GET`  | `/health`         | —                         | `{ "status": "ok" }` |
| `POST` | `/api/chat`       | `{ "question": "..." }`    | `{ "answer": "...", "sources": ["HR Policy", ...] }` |
| `POST` | `/api/upload`     | `multipart/form-data` (`file`) | `{ "filename": "...", "source_name": "...", "chunks_added": 12 }` |
| `GET`  | `/api/documents`  | —                         | `{ "documents": [{ "source_file", "source_name", "chunks" }, ...] }` |

Validation: `/api/chat` requires non-empty `question` (422 otherwise). `/api/upload` rejects requests without/with a wrong `X-Admin-Key` (401), non-`.pdf` (400), files missing the `%PDF-` magic bytes (400), files over `MAX_UPLOAD_MB` (413), empty files (400), and image-only PDFs with no extractable text (422).

---

## Security

| Layer | Mechanism |
|---|---|
| Upload authorization | `POST /api/upload` requires an `X-Admin-Key` header matching the backend's `ADMIN_API_KEY` env var. When `ADMIN_API_KEY` is empty, the endpoint is open (development mode). The Document Upload tab has a "🔒 Admin key" field that persists the key to `localStorage` and adds it to every upload request. |
| Rate limiting | [`slowapi`](https://pypi.org/project/slowapi/) enforces per-IP limits. Defaults: `RATE_LIMIT_CHAT=20/minute`, `RATE_LIMIT_UPLOAD=5/minute`. Excess requests get HTTP 429. Protects OpenAI budget from accidental loops or abuse. |
| Upload hardening | (a) extension must be `.pdf`, (b) `Content-Length`-equivalent body size must be ≤ `MAX_UPLOAD_MB` (default 5 MB) → 413, (c) the body must start with the `%PDF-` magic bytes → 400 if not. Stops trivially-malicious uploads even when the admin key is leaked. |
| Secrets | All credentials live in `backend/.env`, which is `.gitignored`. No secret is shipped to the frontend bundle; the admin key is entered by the user at runtime and lives only in their browser's `localStorage`. |
| CORS | Restricted to `http://localhost:5173` / `127.0.0.1:5173` (the Vite dev origin). |

---

## Sample queries that should work after `python -m app.ingest`

- *"What is the annual leave policy at SWS AI?"* → cites Leave Policy
- *"How many days of sick leave do employees get?"* → cites Leave Policy
- *"What is the notice period for resignation?"* → cites Resignation & Exit Policy
- *"What tools does SWS AI use for communication?"* → cites Employee Onboarding Guide / Company Overview
- *"What is the password policy for company systems?"* → cites IT & Security Policy
- *"How are performance reviews conducted?"* → cites Performance Review Policy
- *"What are the WFH guidelines?"* → cites Work From Home Policy
- *"Does SWS AI offer health insurance?"* → cites Benefits & Compensation
- *"What's the weather today?"* → `"I don't have that information in the company documents."` with no sources (out-of-scope guardrail)

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · uvicorn · pydantic-settings · python-multipart |
| RAG | OpenAI (`text-embedding-3-small`, `gpt-4o-mini`) · ChromaDB · langchain-text-splitters · pypdf |
| Frontend | React 19 · TypeScript · Vite 6 · Livvic (Google Fonts) · hand-rolled CSS |

---

## Future work

- Streaming responses via Server-Sent Events for nicer perceived latency.
- Show per-chunk page numbers in the source badges (data is already in the metadata).
- A small admin endpoint to delete an indexed document.
- Persist the user-facing conversation history to localStorage or a backend store.
