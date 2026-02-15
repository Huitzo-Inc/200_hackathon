"""
Test fixtures for the Lead Engine pack.

Provides mock implementations of all Huitzo SDK services (storage, LLM,
email, HTTP) so tests run without external dependencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from uuid import uuid4

import pytest

from huitzo_sdk import Context, InMemoryBackend


# ---------------------------------------------------------------------------
# Mock backends
# ---------------------------------------------------------------------------


@dataclass
class MockLLMBackend:
    """Mock LLM backend that returns configurable responses."""

    responses: list[str] = field(default_factory=list)
    _call_count: int = 0
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def complete(self, *, prompt: str, **kwargs: Any) -> str:
        self.calls.append({"prompt": prompt, **kwargs})
        if self._call_count < len(self.responses):
            resp = self.responses[self._call_count]
            self._call_count += 1
            return resp
        # Default: return a valid scoring response
        return json.dumps(
            {
                "score": 75,
                "tier": "hot",
                "reasoning": "Strong company fit with good contact quality.",
                "strengths": ["Established company", "Decision-maker contact"],
                "concerns": ["Limited data available"],
            }
        )

    def stream(self, **kwargs: Any) -> AsyncIterator[str]:
        raise NotImplementedError("Streaming not used in lead engine")


@dataclass
class MockEmailBackend:
    """Mock email backend that records sent emails."""

    sent: list[dict[str, Any]] = field(default_factory=list)

    async def send(
        self,
        *,
        to: str | list[str],
        subject: str,
        body: str | None = None,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> None:
        self.sent.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "html": html,
                "cc": cc,
                "bcc": bcc,
            }
        )

    async def send_template(
        self,
        *,
        to: str | list[str],
        template_id: str,
        template_data: dict[str, Any] | None = None,
    ) -> None:
        self.sent.append(
            {"to": to, "template_id": template_id, "template_data": template_data}
        )


@dataclass
class MockHTTPBackend:
    """Mock HTTP backend that returns configurable responses."""

    responses: dict[str, Any] = field(default_factory=dict)
    calls: list[dict[str, Any]] = field(default_factory=list)
    fail: bool = False

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, bytes] | None = None,
        timeout: int | None = None,
    ) -> Any:
        self.calls.append({"method": method, "url": url, "params": params})
        if self.fail:
            raise ConnectionError("Mock HTTP failure")
        return self.responses.get(url, {})


# ---------------------------------------------------------------------------
# Storage wrapper that exposes InMemoryBackend as ctx.storage
# ---------------------------------------------------------------------------


class StorageWrapper:
    """Wraps InMemoryBackend to provide the ctx.storage interface."""

    def __init__(self, backend: InMemoryBackend) -> None:
        self._backend = backend

    async def save(
        self,
        key: str,
        value: Any,
        *,
        ttl: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return await self._backend.save(key, value, ttl=ttl, metadata=metadata)

    async def get(self, key: str, *, default: Any = None) -> Any:
        return await self._backend.get(key, default=default)

    async def delete(self, key: str) -> bool:
        return await self._backend.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._backend.exists(key)

    async def list(
        self, prefix: str = "", *, limit: int = 100, offset: int = 0
    ) -> list[str]:
        return await self._backend.list(prefix, limit=limit, offset=offset)

    async def query(
        self,
        prefix: str = "",
        *,
        metadata: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return await self._backend.query(prefix, metadata=metadata, limit=limit)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def storage_backend() -> InMemoryBackend:
    return InMemoryBackend()


@pytest.fixture
def llm_backend() -> MockLLMBackend:
    return MockLLMBackend()


@pytest.fixture
def email_backend() -> MockEmailBackend:
    return MockEmailBackend()


@pytest.fixture
def http_backend() -> MockHTTPBackend:
    return MockHTTPBackend()


@pytest.fixture
def ctx(
    storage_backend: InMemoryBackend,
    llm_backend: MockLLMBackend,
    email_backend: MockEmailBackend,
    http_backend: MockHTTPBackend,
) -> Context:
    """Build a fully-wired test Context with mock services."""
    from huitzo_sdk import EmailClient, HTTPClient, LLMClient

    context = Context(
        user_id=uuid4(),
        tenant_id=uuid4(),
        command_name="test",
        namespace="leads",
        _llm=LLMClient(_backend=llm_backend),
        _email=EmailClient(_backend=email_backend),
        _http=HTTPClient(_backend=http_backend),
    )
    # Monkey-patch storage onto context for the hackathon
    # (storage is a future stub in the real SDK, but we wire it here for demos)
    object.__setattr__(context, "storage", StorageWrapper(storage_backend))
    return context
