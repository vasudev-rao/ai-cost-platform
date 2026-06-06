"""
Kafka Consumer for LLM Cost Events
Processes events and persists to PostgreSQL via async batch inserts
"""
import asyncio
import json
import logging
from typing import List
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
BATCH_TIMEOUT_SECONDS = 5


class CostEventConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str = "cost-aggregator",
        topics: List[str] = None,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics or ["llm_costs"]
        self.consumer = None
        self._running = False

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=False,  # Manual commit for reliability
            max_poll_records=BATCH_SIZE,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
        )
        await self.consumer.start()
        self._running = True
        logger.info(f"Consumer started | group={self.group_id} | topics={self.topics}")

    async def stop(self):
        self._running = False
        if self.consumer:
            await self.consumer.stop()

    async def process_batch(self, messages: list) -> int:
        """Override in subclass to implement processing logic"""
        processed = 0
        for msg in messages:
            try:
                event = msg.value
                # Process event (store to DB, trigger alerts, etc.)
                logger.debug(f"Processing: org={event.get('organization_id')} model={event.get('model')}")
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
        return processed

    async def run(self):
        batch = []
        last_flush = asyncio.get_event_loop().time()

        try:
            async for message in self.consumer:
                batch.append(message)

                should_flush = (
                    len(batch) >= BATCH_SIZE
                    or (asyncio.get_event_loop().time() - last_flush) > BATCH_TIMEOUT_SECONDS
                )

                if should_flush and batch:
                    try:
                        await self.process_batch(batch)
                        await self.consumer.commit()
                        batch.clear()
                        last_flush = asyncio.get_event_loop().time()
                    except Exception as e:
                        logger.error(f"Batch processing failed: {e}")
                        # Don't commit — reprocess on restart

        except asyncio.CancelledError:
            if batch:
                await self.process_batch(batch)
                await self.consumer.commit()
        finally:
            await self.stop()
