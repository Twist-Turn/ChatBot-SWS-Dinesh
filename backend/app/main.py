"""FastAPI HTTP layer for the SWS AI RAG chatbot."""
from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.indexer import index_pdf, list_indexed_documents
from app.rag import answer
from app.sources import friendly_name

app = FastAPI(title="SWS AI Document Hub", version="0.1.0")

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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = answer(req.question)
    return ChatResponse(**result)


@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

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
