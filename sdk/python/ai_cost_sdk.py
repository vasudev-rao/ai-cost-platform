"""
AI Cost Intelligence Platform — Python SDK
Drop-in wrapper for OpenAI, Anthropic, and other LLM clients.
Automatically tracks all requests and sends cost events to the platform.

Usage:
    from ai_cost_sdk import AIcostClient

    client = AIcostClient(
        api_key="your-project-api-key",
        platform_url="https://api.aicostplatform.com",
        org_id="your-org-id",
        project_id="your-project-id",
    )

    # Wrap OpenAI
    openai_client = client.wrap_openai(openai.OpenAI(api_key="sk-..."))
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    # Cost automatically tracked!
"""

import time
import uuid
import logging
import threading
import queue
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("ai_cost_sdk")


@dataclass
class CostEvent:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    status: str = "success"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    environment: str = "production"
    endpoint: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    is_streaming: bool = False
    error_code: Optional[str] = None


class AIcostClient:
    """
    Main SDK client. Wraps LLM clients to auto-track costs.
    Uses background thread with queue for non-blocking event ingestion.
    """

    def __init__(
        self,
        api_key: str,
        platform_url: str,
        org_id: str,
        project_id: str,
        environment: str = "production",
        batch_size: int = 50,
        flush_interval_seconds: float = 5.0,
        timeout_seconds: float = 10.0,
        disabled: bool = False,
    ):
        self.api_key = api_key
        self.platform_url = platform_url.rstrip("/")
        self.org_id = org_id
        self.project_id = project_id
        self.environment = environment
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        self.timeout = timeout_seconds
        self.disabled = disabled

        self._queue: queue.Queue = queue.Queue(maxsize=10_000)
        self._shutdown = threading.Event()

        if not disabled:
            self._flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
            self._flush_thread.start()

    def track(self, event: CostEvent) -> None:
        """Non-blocking event tracking — adds to queue and returns immediately."""
        if self.disabled:
            return
        event.environment = event.environment or self.environment
        try:
            self._queue.put_nowait(asdict(event))
        except queue.Full:
            logger.warning("AI Cost SDK queue full — dropping event")

    def _flush_worker(self) -> None:
        """Background thread: batches events and sends to platform."""
        while not self._shutdown.is_set():
            batch: List[Dict] = []
            deadline = time.time() + self.flush_interval

            while time.time() < deadline and len(batch) < self.batch_size:
                try:
                    event = self._queue.get(timeout=0.1)
                    batch.append(event)
                except queue.Empty:
                    break

            if batch:
                self._send_batch(batch)

    def _send_batch(self, events: List[Dict]) -> None:
        """Send batch of events to the platform API."""
        if not HAS_HTTPX:
            return
        try:
            for event in events:
                url = f"{self.platform_url}/api/v1/costs/ingest?org_id={self.org_id}&project_id={self.project_id}"
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(
                        url,
                        json=event,
                        headers={"X-API-Key": self.api_key},
                    )
        except Exception as e:
            logger.error(f"Failed to send cost events: {e}")

    def shutdown(self, timeout: float = 5.0) -> None:
        """Flush remaining events and shut down background thread."""
        self._shutdown.set()
        remaining = []
        while not self._queue.empty():
            try:
                remaining.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if remaining:
            self._send_batch(remaining)
        self._flush_thread.join(timeout=timeout)

    def wrap_openai(self, openai_client: Any) -> "OpenAIWrapper":
        return OpenAIWrapper(openai_client, self)

    def wrap_anthropic(self, anthropic_client: Any) -> "AnthropicWrapper":
        return AnthropicWrapper(anthropic_client, self)

    # Context manager support
    def __enter__(self): return self
    def __exit__(self, *args): self.shutdown()


class OpenAIWrapper:
    """Transparent wrapper for openai.OpenAI that tracks costs."""

    def __init__(self, client: Any, tracker: AIcostClient):
        self._client = client
        self._tracker = tracker
        self.chat = self._ChatCompletions(client.chat, tracker)
        self.embeddings = self._Embeddings(client.embeddings, tracker)

    class _ChatCompletions:
        def __init__(self, chat: Any, tracker: AIcostClient):
            self._chat = chat
            self._tracker = tracker

        def create(self, **kwargs) -> Any:
            start = time.time()
            model = kwargs.get("model", "unknown")
            is_streaming = kwargs.get("stream", False)
            try:
                response = self._chat.completions.create(**kwargs)
                latency_ms = int((time.time() - start) * 1000)
                usage = getattr(response, "usage", None)
                self._tracker.track(CostEvent(
                    provider="openai",
                    model=model,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0),
                    completion_tokens=getattr(usage, "completion_tokens", 0),
                    latency_ms=latency_ms,
                    is_streaming=is_streaming,
                    request_id=getattr(response, "id", None),
                ))
                return response
            except Exception as e:
                latency_ms = int((time.time() - start) * 1000)
                self._tracker.track(CostEvent(
                    provider="openai", model=model,
                    prompt_tokens=0, completion_tokens=0,
                    latency_ms=latency_ms, status="error",
                    error_code=type(e).__name__,
                ))
                raise

    class _Embeddings:
        def __init__(self, embeddings: Any, tracker: AIcostClient):
            self._embeddings = embeddings
            self._tracker = tracker

        def create(self, **kwargs) -> Any:
            start = time.time()
            model = kwargs.get("model", "text-embedding-ada-002")
            response = self._embeddings.create(**kwargs)
            latency_ms = int((time.time() - start) * 1000)
            usage = getattr(response, "usage", None)
            self._tracker.track(CostEvent(
                provider="openai", model=model,
                prompt_tokens=getattr(usage, "total_tokens", 0),
                completion_tokens=0,
                latency_ms=latency_ms,
            ))
            return response


class AnthropicWrapper:
    """Transparent wrapper for anthropic.Anthropic that tracks costs."""

    def __init__(self, client: Any, tracker: AIcostClient):
        self._client = client
        self._tracker = tracker
        self.messages = self._Messages(client.messages, tracker)

    class _Messages:
        def __init__(self, messages: Any, tracker: AIcostClient):
            self._messages = messages
            self._tracker = tracker

        def create(self, **kwargs) -> Any:
            start = time.time()
            model = kwargs.get("model", "unknown")
            try:
                response = self._messages.create(**kwargs)
                latency_ms = int((time.time() - start) * 1000)
                usage = getattr(response, "usage", None)
                self._tracker.track(CostEvent(
                    provider="anthropic", model=model,
                    prompt_tokens=getattr(usage, "input_tokens", 0),
                    completion_tokens=getattr(usage, "output_tokens", 0),
                    latency_ms=latency_ms,
                    request_id=getattr(response, "id", None),
                ))
                return response
            except Exception as e:
                latency_ms = int((time.time() - start) * 1000)
                self._tracker.track(CostEvent(
                    provider="anthropic", model=model,
                    prompt_tokens=0, completion_tokens=0,
                    latency_ms=latency_ms, status="error",
                    error_code=type(e).__name__,
                ))
                raise
