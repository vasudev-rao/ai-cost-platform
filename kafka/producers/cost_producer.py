"""
Kafka Producer for LLM Cost Events
Supports both sync and async production with exactly-once semantics
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from kafka.schemas.llm_event import LLMCostEvent

logger = logging.getLogger(__name__)


class CostEventProducer:
    def __init__(self, bootstrap_servers: str, topic: str = "llm_costs"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            compression_type="lz4",
            acks="all",  # Wait for all replicas
            enable_idempotence=True,  # Exactly-once
            max_batch_size=32768,
            linger_ms=10,  # Micro-batching
            request_timeout_ms=30000,
            retry_backoff_ms=100,
        )
        await self.producer.start()
        logger.info(f"Producer started for topic: {self.topic}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_cost_event(self, event: LLMCostEvent) -> bool:
        if not self.producer:
            raise RuntimeError("Producer not started")

        try:
            # Partition key = organization_id for ordered processing per org
            await self.producer.send_and_wait(
                self.topic,
                key=event.organization_id,
                value=event.dict(),
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to produce cost event: {e}")
            await self._send_to_dlq(event.dict(), str(e))
            return False

    async def send_batch(self, events: list) -> int:
        tasks = [self.send_cost_event(e) for e in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return sum(1 for r in results if r is True)

    async def _send_to_dlq(self, event: dict, error: str):
        try:
            dlq_event = {**event, "dlq_error": error, "dlq_timestamp": str(uuid.uuid4())}
            await self.producer.send("llm_dlq", value=dlq_event)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
