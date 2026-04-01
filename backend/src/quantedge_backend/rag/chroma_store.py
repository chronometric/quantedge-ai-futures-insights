"""Chroma persistent client and embedding function selection."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from quantedge_backend.settings import Settings

_COLLECTION = "quantedge_kb_v1"


def get_embedding_function(settings: Settings) -> Any:
    if settings.openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(  # type: ignore[attr-defined]
            api_key=settings.openai_api_key,
            model_name=settings.rag_embedding_model,
        )
    return embedding_functions.DefaultEmbeddingFunction()


def get_kb_collection(settings: Settings) -> Any:
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    ef = get_embedding_function(settings)
    return client.get_or_create_collection(name=_COLLECTION, embedding_function=ef)
