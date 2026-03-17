from __future__ import annotations

from fastapi import FastAPI, Request

from sentinel.config import SentinelConfig
from sentinel.factory import build_llm_client, build_verifier
from sentinel.middleware import SentinelMiddleware
from sentinel.schemas import ChatRequest, ChatResponse


def create_app() -> FastAPI:
    app = FastAPI(title="Sentinel Demo")

    config = SentinelConfig.from_env()
    if config.safe_message == "Security Safe: response blocked by Sentinel.":
        config.safe_message = (
            "Security Safe: Sentinel blocked a possible hallucination or data leak."
        )

    verifier = build_verifier(config)
    llm_client = build_llm_client(config)

    app.add_middleware(SentinelMiddleware, verifier=verifier)

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
        source_document = payload.source_document or verifier.config.source_document
        request.state.source_document = source_document
        answer = await llm_client.generate(payload.prompt, source_document)
        return ChatResponse(answer=answer)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
