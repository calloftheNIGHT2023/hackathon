from __future__ import annotations

import os
from typing import List, Literal

from pydantic import BaseModel, Field


class SentinelConfig(BaseModel):
    """Runtime configuration for the Sentinel firewall."""

    safe_message: str = "Security Safe: response blocked by Sentinel."
    source_document: str = (
        "Only share information present in this document. "
        "There are no passwords, secrets, SSNs, or internal codenames."
    )
    blocked_keywords: List[str] = Field(default_factory=lambda: ["Project X"])
    blocked_regexes: List[str] = Field(
        default_factory=lambda: [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"(?i)\b(password\s*[:=]\s*\S+)",
            r"(?i)\b(api[_ -]?key\s*[:=]\s*\S+)",
        ]
    )
    response_field: str = "answer"
    upstream_mode: Literal["mock", "openai"] = "mock"
    judge_mode: Literal["mock", "langchain"] = "mock"
    upstream_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    upstream_temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "SentinelConfig":
        return cls(
            safe_message=os.getenv(
                "SENTINEL_SAFE_MESSAGE",
                "Security Safe: response blocked by Sentinel.",
            ),
            source_document=os.getenv(
                "SENTINEL_SOURCE_DOCUMENT",
                "Only share information present in this document. "
                "There are no passwords, secrets, SSNs, or internal codenames.",
            ),
            blocked_keywords=_split_csv(
                os.getenv("SENTINEL_BLOCKED_KEYWORDS", "Project X")
            ),
            upstream_mode=os.getenv("SENTINEL_UPSTREAM_MODE", "mock"),
            judge_mode=os.getenv("SENTINEL_JUDGE_MODE", "mock"),
            upstream_model=os.getenv("SENTINEL_UPSTREAM_MODEL", "gpt-4o-mini"),
            judge_model=os.getenv("SENTINEL_JUDGE_MODEL", "gpt-4o-mini"),
            upstream_temperature=float(
                os.getenv("SENTINEL_UPSTREAM_TEMPERATURE", "0.0")
            ),
        )


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
