"""structlog configuration."""

from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import Processor

from quantedge_backend.settings import Settings


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    shared: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if settings.log_json:
        processors: list[Processor] = [*shared, structlog.processors.JSONRenderer()]
    else:
        processors = [*shared, structlog.dev.ConsoleRenderer(colors=True)]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
