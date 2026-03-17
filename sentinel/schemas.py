from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    source_document: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    status: Literal["ok", "blocked"] = "ok"
    reason: Optional[str] = None


class VerificationResult(BaseModel):
    allowed: bool
    reason: str
    method: Literal["regex", "self-correction", "pass"]

