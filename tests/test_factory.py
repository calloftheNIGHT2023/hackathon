from __future__ import annotations

from sentinel.config import SentinelConfig
from sentinel.factory import build_llm_client, build_verifier
from sentinel.llm_clients import FakeOpenAIClient
from sentinel.verification import MockJudge, SentinelVerifier


def test_factory_builds_mock_components_by_default() -> None:
    config = SentinelConfig()

    client = build_llm_client(config)
    verifier = build_verifier(config)

    assert isinstance(client, FakeOpenAIClient)
    assert isinstance(verifier, SentinelVerifier)
    assert isinstance(verifier.judge, MockJudge)
