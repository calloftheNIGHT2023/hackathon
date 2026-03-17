from __future__ import annotations

import abc
from typing import Optional


class BaseLLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str, source_document: Optional[str] = None) -> str:
        """Generate a response from the upstream model."""


class FakeOpenAIClient(BaseLLMClient):
    """
    Offline demo client that intentionally leaks a fake secret.
    """

    async def generate(self, prompt: str, source_document: Optional[str] = None) -> str:
        if "password" in prompt.lower() or "secret" in prompt.lower():
            return "Internal note: the admin password is hunter2 for Project X."
        return "The source document contains no passwords or sensitive records."


class OpenAIChatClient(BaseLLMClient):
    """
    Optional production client backed by LangChain ChatOpenAI.
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0) -> None:
        from langchain_openai import ChatOpenAI

        self._client = ChatOpenAI(model=model, temperature=temperature)

    async def generate(self, prompt: str, source_document: Optional[str] = None) -> str:
        guarded_prompt = self._build_prompt(prompt, source_document)
        result = await self._client.ainvoke(guarded_prompt)
        return getattr(result, "content", str(result))

    @staticmethod
    def _build_prompt(prompt: str, source_document: Optional[str]) -> str:
        if not source_document:
            return prompt

        return (
            "Answer the user using only the source document below. "
            "Do not invent facts. Do not reveal credentials, private identifiers, "
            "or internal codenames unless they are explicitly present in the source.\n\n"
            f"Source Document:\n{source_document}\n\n"
            f"User Request:\n{prompt}"
        )
