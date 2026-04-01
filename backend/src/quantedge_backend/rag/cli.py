"""CLI: ``python -m quantedge_backend.rag.cli ingest``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from quantedge_backend.rag.ingest import ingest_kb
from quantedge_backend.settings import clear_settings_cache, get_settings

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="QuantEdge knowledge base tools")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest_p = sub.add_parser("ingest", help="Embed markdown under KB_DIR into Chroma")
    ingest_p.add_argument(
        "--kb-dir",
        type=Path,
        default=None,
        help="Override KB directory (default: KB_DIR env / settings)",
    )
    args = parser.parse_args()
    if args.command == "ingest":
        clear_settings_cache()
        settings = get_settings()
        n = ingest_kb(settings, kb_dir=args.kb_dir)
        logging.info("Ingested %s chunks into %s", n, settings.chroma_persist_dir)


if __name__ == "__main__":
    main()
