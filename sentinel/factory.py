from __future__ import annotations

from sentinel.config import SentinelConfig
from sentinel.llm_clients import BaseLLMClient, FakeOpenAIClient, OpenAIChatClient
from sentinel.verification import LangChainJudge, MockJudge, SentinelVerifier


def build_llm_client(config: SentinelConfig) -> BaseLLMClient:
    if config.upstream_mode == "openai":
        return OpenAIChatClient(
            model=config.upstream_model,
            temperature=config.upstream_temperature,
        )
    return FakeOpenAIClient()


def build_verifier(config: SentinelConfig) -> SentinelVerifier:
    if config.judge_mode == "langchain":
        from langchain_openai import ChatOpenAI

        judge_model = ChatOpenAI(model=config.judge_model, temperature=0.0)
        judge = LangChainJudge(judge_model)
    else:
        judge = MockJudge(forbidden_terms=["hunter2", *config.blocked_keywords])

    return SentinelVerifier(config=config, judge=judge)

