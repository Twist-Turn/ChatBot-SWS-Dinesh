"""Shared indexing pipeline: PDF bytes -> chunks -> embeddings -> Chroma."""
from __future__ import annotations

import uuid
from io import BytesIO

import chromadb
from chromadb.api.models.Collection import Collection
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

from app.config import settings
from app.sources import friendly_name

_openai_client: OpenAI | None = None
_chroma_client: chromadb.PersistentClient | None = None


def openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return _chroma_client


def get_collection() -> Collection:
    return chroma_client().get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection() -> Collection:
    """Drop and recreate the collection. Used by the ingest CLI for clean rebuilds."""
    client = chroma_client()
    try:
        client.delete_collection(settings.chroma_collection)
    except Exception:
        pass
    return get_collection()


def _extract_pages(data: bytes) -> list[tuple[int, str]]:
    reader = PdfReader(BytesIO(data))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def _embed_batch(texts: list[str]) -> list[list[float]]:
    resp = openai_client().embeddings.create(
        model=settings.openai_embed_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def index_pdf(*, filename: str, data: bytes, collection: Collection | None = None) -> int:
    """Chunk + embed + upsert a single PDF. Returns number of chunks added."""
    if collection is None:
        collection = get_collection()

    pages = _extract_pages(data)
    if not pages:
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    name = friendly_name(filename)
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    chunk_index = 0
    for page_num, page_text in pages:
        for piece in splitter.split_text(page_text):
            piece = piece.strip()
            if not piece:
                continue
            documents.append(piece)
            metadatas.append(
                {
                    "source_file": filename,
                    "source_name": name,
                    "page": page_num,
                    "chunk_index": chunk_index,
                }
            )
            ids.append(f"{filename}:{page_num}:{chunk_index}:{uuid.uuid4().hex[:8]}")
            chunk_index += 1

    if not documents:
        return 0

    try:
        collection.delete(where={"source_file": filename})
    except Exception:
        pass

    batch_size = 64
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        embeddings = _embed_batch(batch_docs)
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_meta,
            embeddings=embeddings,
        )

    return len(documents)


def list_indexed_documents() -> list[dict]:
    """Return deduplicated [{source_name, source_file, chunks}] for the upload UI."""
    collection = get_collection()
    result = collection.get(include=["metadatas"])
    by_file: dict[str, dict] = {}
    for m in result.get("metadatas") or []:
        if not m:
            continue
        source_file = m.get("source_file", "unknown")
        source_name = m.get("source_name", source_file)
        entry = by_file.setdefault(
            source_file,
            {"source_file": source_file, "source_name": source_name, "chunks": 0},
        )
        entry["chunks"] += 1
    return sorted(by_file.values(), key=lambda x: x["source_name"])
