"""FastAPI HTTP layer for the SWS AI RAG chatbot."""
from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.indexer import index_pdf, list_indexed_documents
from app.rag import answer
from app.sources import friendly_name

PDF_MAGIC = b"%PDF-"
MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="SWS AI Document Hub", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Reject upload requests that don't carry the configured admin key.

    If ADMIN_API_KEY is empty, the endpoint is open (development mode) so the
    bundled ingest CLI and a fresh clone work without configuration.
    """
    expected = settings.admin_api_key
    if not expected:
        return
    if not x_admin_key or x_admin_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header.")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class UploadResponse(BaseModel):
    filename: str
    source_name: str
    chunks_added: int


class DocumentEntry(BaseModel):
    source_file: str
    source_name: str
    chunks: int


class DocumentsResponse(BaseModel):
    documents: list[DocumentEntry]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    auth_enabled: bool


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", auth_enabled=bool(settings.admin_api_key))


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_chat)
def chat(request: Request, req: ChatRequest) -> ChatResponse:
    result = answer(req.question)
    return ChatResponse(**result)


@app.post("/api/upload", response_model=UploadResponse, dependencies=[Depends(require_admin_key)])
@limiter.limit(settings.rate_limit_upload)
async def upload(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
        )

    if not data.startswith(PDF_MAGIC):
        raise HTTPException(
            status_code=400,
            detail="File does not look like a real PDF (missing %PDF- magic bytes).",
        )

    try:
        added = index_pdf(filename=filename, data=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to index PDF: {exc}") from exc

    if added == 0:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the PDF (it may be scanned/image-based).",
        )

    return UploadResponse(
        filename=filename,
        source_name=friendly_name(filename),
        chunks_added=added,
    )


@app.get("/api/documents", response_model=DocumentsResponse)
def documents() -> DocumentsResponse:
    return DocumentsResponse(documents=[DocumentEntry(**d) for d in list_indexed_documents()])
