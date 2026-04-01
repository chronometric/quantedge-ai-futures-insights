"""Split markdown files into chunks with optional YAML-style frontmatter."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TextChunk:
    chunk_id: str
    text: str
    metadata: dict[str, str]
    source_path: str


_FRONTMATTER = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.DOTALL)


def _parse_meta_block(block: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def parse_markdown_file(path: Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    m = _FRONTMATTER.match(raw.strip())
    if not m:
        return {}, raw
    meta = _parse_meta_block(m.group(1))
    body = m.group(2).strip()
    return meta, body


def split_body(body: str, *, max_chars: int = 900) -> list[str]:
    """Split long bodies on paragraph boundaries."""
    if len(body) <= max_chars:
        return [body]
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for para in body.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if size + len(p) + 2 > max_chars and buf:
            parts.append("\n\n".join(buf))
            buf = [p]
            size = len(p)
        else:
            buf.append(p)
            size += len(p) + 2
    if buf:
        parts.append("\n\n".join(buf))
    return parts


def chunk_kb_file(path: Path) -> list[TextChunk]:
    """One file → one or more :class:`TextChunk` records."""
    meta, body = parse_markdown_file(path)
    base_id = meta.get("chunk_id") or path.stem
    splits = split_body(body)
    out: list[TextChunk] = []
    for i, text in enumerate(splits):
        cid = base_id if len(splits) == 1 else f"{base_id}_{i + 1:02d}"
        md = {
            "topic": meta.get("topic", "general"),
            "regime": meta.get("regime", "any"),
            "instrument_class": meta.get("instrument_class", "any"),
            "chunk_id": cid,
            "source_path": str(path.as_posix()),
        }
        out.append(TextChunk(chunk_id=cid, text=text, metadata=md, source_path=str(path)))
    return out


def iter_kb_chunks(kb_dir: Path) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for path in sorted(kb_dir.rglob("*.md")):
        chunks.extend(chunk_kb_file(path))
    return chunks
