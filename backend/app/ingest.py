"""One-time ingestion CLI: rebuilds the vector store from ./Documents."""
from __future__ import annotations

from app.config import settings
from app.indexer import index_pdf, reset_collection


def main() -> None:
    docs_dir = settings.documents_dir
    pdfs = sorted(docs_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {docs_dir}")

    print(f"Resetting collection '{settings.chroma_collection}' at {settings.chroma_dir}")
    collection = reset_collection()

    total = 0
    for path in pdfs:
        data = path.read_bytes()
        added = index_pdf(filename=path.name, data=data, collection=collection)
        total += added
        print(f"  {path.name:42s}  {added:4d} chunks")

    print(f"\nDone. {total} chunks across {len(pdfs)} documents.")


if __name__ == "__main__":
    main()
