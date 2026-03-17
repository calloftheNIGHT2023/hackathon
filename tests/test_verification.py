from __future__ import annotations

import asyncio

from sentinel.config import SentinelConfig
from sentinel.verification import MockJudge, SentinelVerifier, _is_yes


def test_regex_check_blocks_sensitive_pattern() -> None:
    verifier = SentinelVerifier(
        config=SentinelConfig(),
        judge=MockJudge(),
    )

    result = asyncio.run(verifier.verify("Customer SSN is 123-45-6789."))

    assert result.allowed is False
    assert result.method == "regex"


def test_self_correction_blocks_unsupported_secret() -> None:
    verifier = SentinelVerifier(
        config=SentinelConfig(),
        judge=MockJudge(forbidden_terms=["hunter2"]),
    )

    result = asyncio.run(
        verifier.verify(
            "The password is hunter2.",
            "The document contains no passwords.",
        )
    )

    assert result.allowed is False
    assert result.method == "self-correction"


def test_verification_passes_supported_statement() -> None:
    verifier = SentinelVerifier(
        config=SentinelConfig(blocked_keywords=[]),
        judge=MockJudge(),
    )

    result = asyncio.run(
        verifier.verify(
            "The employee handbook contains no passwords.",
            "The employee handbook contains no passwords.",
        )
    )

    assert result.allowed is True
    assert result.method == "pass"


def test_yes_parser_is_strict() -> None:
    assert _is_yes("Yes") is True
    assert _is_yes("yes\n") is True
    assert _is_yes("Yes, supported.") is False
    assert _is_yes("No") is False

