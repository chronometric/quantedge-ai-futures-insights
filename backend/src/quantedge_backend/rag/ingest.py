"""Ingest KB markdown into Chroma."""

from __future__ import annotations

import logging
from pathlib import Path

from quantedge_backend.rag.chroma_store import get_kb_collection
from quantedge_backend.rag.chunking import iter_kb_chunks
from quantedge_backend.settings import Settings

logger = logging.getLogger(__name__)


def ingest_kb(settings: Settings, *, kb_dir: Path | None = None) -> int:
    """
    Embed and upsert all ``*.md`` under ``kb_dir`` (defaults to ``settings.kb_dir``).

    Returns number of chunks written.
    """
    root = kb_dir or Path(settings.kb_dir)
    if not root.is_dir():
        msg = f"KB directory not found: {root}"
        raise FileNotFoundError(msg)
    chunks = iter_kb_chunks(root)
    if not chunks:
        logger.warning("No markdown chunks found under %s", root)
        return 0
    col = get_kb_collection(settings)
    ids = [c.chunk_id for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = []
    for c in chunks:
        md = dict(c.metadata)
        md["kb_version"] = settings.kb_version
        metadatas.append(md)
    col.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Ingested %s chunks into Chroma (quantedge_kb_v1)", len(ids))
    return len(ids)
