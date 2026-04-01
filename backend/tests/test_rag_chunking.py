"""KB chunking and frontmatter."""

from __future__ import annotations

from pathlib import Path

from quantedge_backend.rag.chunking import chunk_kb_file, iter_kb_chunks


def test_chunk_kb_file_with_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text(
        "---\n"
        "topic: test\n"
        "regime: any\n"
        "instrument_class: futures\n"
        "chunk_id: unit_test_01\n"
        "---\n\n"
        "# Title\n\nBody paragraph one.\n",
        encoding="utf-8",
    )
    chunks = chunk_kb_file(p)
    assert len(chunks) >= 1
    assert chunks[0].chunk_id == "unit_test_01"
    assert chunks[0].metadata["regime"] == "any"


def test_iter_kb_chunks_repo_samples() -> None:
    kb = Path(__file__).resolve().parents[2] / "kb"
    if not kb.is_dir():
        return
    chunks = iter_kb_chunks(kb)
    assert len(chunks) >= 1
