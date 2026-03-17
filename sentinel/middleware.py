from __future__ import annotations

import json
from typing import Any, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from sentinel.schemas import ChatResponse
from sentinel.verification import SentinelVerifier


class SentinelMiddleware(BaseHTTPMiddleware):
    """
    Intercepts JSON responses and blocks unsafe LLM output before it reaches clients.
    """

    def __init__(self, app, verifier: SentinelVerifier) -> None:
        super().__init__(app)
        self.verifier = verifier

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if "application/json" not in response.headers.get("content-type", ""):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return self._rebuild_response(response, body)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return self._rebuild_response(response, body)

        target_text = self._extract_response_text(payload)
        if target_text is None:
            return self._rebuild_response(response, body)

        source_document = self._extract_source_document(request, payload)
        verification = await self.verifier.verify(target_text, source_document)
        if verification.allowed:
            return self._rebuild_response(response, body)

        safe_payload = ChatResponse(
            answer=self.verifier.config.safe_message,
            status="blocked",
            reason=verification.reason,
        ).model_dump()
        return JSONResponse(status_code=200, content=safe_payload)

    def _extract_response_text(self, payload: Dict[str, Any]) -> Optional[str]:
        value = payload.get(self.verifier.config.response_field)
        return value if isinstance(value, str) else None

    async def _extract_request_json(self, request: Request) -> Dict[str, Any]:
        if not hasattr(request.state, "_sentinel_request_json"):
            try:
                request.state._sentinel_request_json = await request.json()
            except json.JSONDecodeError:
                request.state._sentinel_request_json = {}
        return request.state._sentinel_request_json

    def _extract_source_document(
        self, request: Request, payload: Dict[str, Any]
    ) -> Optional[str]:
        request_source = getattr(request.state, "source_document", None)
        if isinstance(request_source, str):
            return request_source
        payload_source = payload.get("source_document")
        if isinstance(payload_source, str):
            return payload_source
        return None

    @staticmethod
    def _rebuild_response(response: Response, body: bytes) -> Response:
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

