from __future__ import annotations

import abc
import re
from typing import Iterable, Optional

from pydantic import BaseModel

from sentinel.config import SentinelConfig
from sentinel.schemas import VerificationResult


class ConsistencyJudge(abc.ABC):
    @abc.abstractmethod
    async def is_consistent(self, statement: str, source_document: str) -> bool:
        """Return True only when the statement is supported by the source."""


class LangChainJudge(ConsistencyJudge):
    """
    Production judge wrapper.

    Pass any LangChain chat model that supports `ainvoke`, for example:
    `ChatOpenAI(model="gpt-4o-mini")` or a local Llama endpoint adapter.
    """

    def __init__(self, model) -> None:
        from langchain_core.prompts import ChatPromptTemplate

        self._chain = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are Sentinel's verification layer. "
                    "Return Yes only if every material claim in the statement is "
                    "fully supported by the source document. "
                    "Return No if the statement adds unsupported facts, guesses, "
                    "credentials, personal data, internal project names, or any "
                    "confidential detail not explicitly present in the source. "
                    "Answer with exactly one token: Yes or No.",
                ),
                (
                    "human",
                    "Check whether the following statement is factually consistent "
                    "with the source document.\n\n"
                    "Source Document:\n{source_document}\n\n"
                    "Statement:\n{statement}\n\n"
                    "Answer only Yes or No.",
                ),
            ]
        ) | model

    async def is_consistent(self, statement: str, source_document: str) -> bool:
        result = await self._chain.ainvoke(
            {"statement": statement, "source_document": source_document}
        )
        return _is_yes(getattr(result, "content", str(result)))


class MockJudge(ConsistencyJudge):
    """
    Offline demo judge.

    It blocks statements that mention secrets or terms absent from the source.
    """

    def __init__(self, forbidden_terms: Optional[Iterable[str]] = None) -> None:
        self.forbidden_terms = {term.lower() for term in forbidden_terms or []}

    async def is_consistent(self, statement: str, source_document: str) -> bool:
        normalized_statement = statement.lower()
        normalized_source = source_document.lower()

        if any(term in normalized_statement for term in self.forbidden_terms):
            return False

        for token in ["password", "secret", "project x", "ssn", "api key"]:
            if token in normalized_statement and token not in normalized_source:
                return False

        return True


def _is_yes(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized == "yes" or normalized.startswith("yes\n")


class SentinelVerifier(BaseModel):
    config: SentinelConfig
    judge: ConsistencyJudge

    model_config = {"arbitrary_types_allowed": True}

    async def verify(
        self, response_text: str, source_document: Optional[str] = None
    ) -> VerificationResult:
        source = source_document or self.config.source_document
        regex_result = self._regex_keyword_scan(response_text)
        if regex_result is not None:
            return regex_result

        is_consistent = await self.judge.is_consistent(response_text, source)
        if not is_consistent:
            return VerificationResult(
                allowed=False,
                reason="Response failed the self-correction consistency check.",
                method="self-correction",
            )

        return VerificationResult(
            allowed=True,
            reason="Response passed Sentinel verification.",
            method="pass",
        )

    def _regex_keyword_scan(self, response_text: str) -> Optional[VerificationResult]:
        lowered = response_text.lower()

        for keyword in self.config.blocked_keywords:
            if keyword.lower() in lowered:
                return VerificationResult(
                    allowed=False,
                    reason=f"Blocked keyword detected: {keyword}",
                    method="regex",
                )

        for pattern in self.config.blocked_regexes:
            if re.search(pattern, response_text):
                return VerificationResult(
                    allowed=False,
                    reason=f"Blocked sensitive pattern detected: {pattern}",
                    method="regex",
                )

        return None
