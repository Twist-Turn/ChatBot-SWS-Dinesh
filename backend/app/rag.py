"""RAG: embed question -> retrieve top-k -> grounded LLM answer."""
from __future__ import annotations

from typing import TypedDict

from app.config import settings
from app.indexer import get_collection, openai_client
from app.prompts import SYSTEM_PROMPT, build_user_message

FALLBACK = "I don't have that information in the company documents."


class Answer(TypedDict):
    answer: str
    sources: list[str]


def _embed_question(question: str) -> list[float]:
    resp = openai_client().embeddings.create(
        model=settings.openai_embed_model,
        input=[question],
    )
    return resp.data[0].embedding


def _retrieve(question: str, k: int) -> tuple[list[str], list[dict]]:
    collection = get_collection()
    embedding = _embed_question(question)
    result = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        include=["documents", "metadatas"],
    )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    return docs, metas


def _format_context(docs: list[str], metas: list[dict]) -> str:
    blocks = []
    for doc, meta in zip(docs, metas):
        name = (meta or {}).get("source_name", "Unknown")
        page = (meta or {}).get("page", "?")
        blocks.append(f"[Source: {name} | Page {page}]\n{doc}")
    return "\n\n".join(blocks)


def _dedupe_sources(metas: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for m in metas:
        name = (m or {}).get("source_name")
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def answer(question: str) -> Answer:
    question = (question or "").strip()
    if not question:
        return {"answer": "Please enter a question.", "sources": []}

    docs, metas = _retrieve(question, settings.retrieval_k)
    if not docs:
        return {"answer": FALLBACK, "sources": []}

    context = _format_context(docs, metas)
    user_message = build_user_message(context, question)

    completion = openai_client().chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )
    text = (completion.choices[0].message.content or "").strip()

    sources = [] if text == FALLBACK else _dedupe_sources(metas)
    return {"answer": text, "sources": sources}


if __name__ == "__main__":
    import json
    import sys

    q = " ".join(sys.argv[1:]) or "What is the leave policy?"
    print(json.dumps(answer(q), indent=2))
