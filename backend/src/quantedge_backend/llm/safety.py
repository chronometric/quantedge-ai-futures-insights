"""Post-process insights for compliance-style guardrails (V1 heuristics)."""

from __future__ import annotations

import copy
import re
from typing import Any

_FORBIDDEN = re.compile(
    r"\b(guaranteed|risk-?free|cannot lose|sure thing|100%\s*certain|no risk)\b",
    re.IGNORECASE,
)


def apply_safety_guardrails(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Deep-copy and soften risky phrasing; append machine-readable risk notes.

    This is not legal review — production deployments still need counsel-approved copy.
    """
    out = copy.deepcopy(payload)
    narrative = out.get("narrative") or {}
    summary = str(narrative.get("summary", ""))
    hits = _FORBIDDEN.findall(summary)
    structured = out.setdefault("structured", {})
    risk_notes = list(structured.get("risk_notes") or [])
    if hits:
        risk_notes.append(
            "Automated guardrail: summary contained promotional certainty language; "
            "interpret as educational only.",
        )
    if _FORBIDDEN.search(summary):
        narrative["summary"] = _FORBIDDEN.sub(
            "[redacted: avoid certainty claims]",
            summary,
        )
    structured["risk_notes"] = risk_notes
    out["narrative"] = narrative
    base = str(out.get("disclaimer") or "").strip()
    suffix = "Outputs are not personalized investment advice."
    if suffix not in base:
        out["disclaimer"] = f"{base} {suffix}".strip() if base else suffix
    return out
