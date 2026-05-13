"""Conversation memory backed by Redis when available, dict otherwise.

The fallback exists so the demo runs end-to-end on a laptop that has
no Redis instance. The interface is intentionally minimal — we only
need a per-session ring buffer of message dicts.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from typing import Deque, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("aegis.ai.memory")


class _InMemoryStore:
    def __init__(self, max_turns: int = 20) -> None:
        self._buckets: Dict[str, Deque[dict]] = {}
        self._max = max_turns
        self._lock = asyncio.Lock()

    async def append(self, session_id: str, message: dict) -> None:
        async with self._lock:
            buf = self._buckets.setdefault(session_id, deque(maxlen=self._max))
            buf.append(message)

    async def load(self, session_id: str) -> List[dict]:
        async with self._lock:
            return list(self._buckets.get(session_id, []))

    async def clear(self, session_id: str) -> None:
        async with self._lock:
            self._buckets.pop(session_id, None)


class _RedisStore:  # pragma: no cover - requires running Redis
    def __init__(self, url: str, max_turns: int = 20) -> None:
        import redis.asyncio as redis  # type: ignore

        self._client = redis.from_url(url, decode_responses=True)
        self._max = max_turns

    def _key(self, session_id: str) -> str:
        return f"aegis:conv:{session_id}"

    async def append(self, session_id: str, message: dict) -> None:
        key = self._key(session_id)
        await self._client.rpush(key, json.dumps(message, ensure_ascii=False))
        await self._client.ltrim(key, -self._max, -1)
        await self._client.expire(key, 60 * 60 * 24 * 3)  # 3 days

    async def load(self, session_id: str) -> List[dict]:
        items = await self._client.lrange(self._key(session_id), 0, -1)
        return [json.loads(x) for x in items]

    async def clear(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))


class ConversationMemory:
    """Public facade — chooses Redis if reachable, else in-memory."""

    def __init__(self) -> None:
        self._store = _InMemoryStore()
        self._redis: Optional[_RedisStore] = None
        if settings.redis_url:
            try:
                self._redis = _RedisStore(settings.redis_url)
                logger.info("ConversationMemory: Redis backend = %s", settings.redis_url)
            except Exception as e:  # noqa: BLE001
                logger.info("Redis unavailable, using in-memory fallback (%s)", e)

    async def append(self, session_id: str, role: str, content: str) -> None:
        msg = {"role": role, "content": content}
        if self._redis:
            try:
                await self._redis.append(session_id, msg)
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("Redis append failed, falling back: %s", e)
        await self._store.append(session_id, msg)

    async def load(self, session_id: str) -> List[dict]:
        if self._redis:
            try:
                return await self._redis.load(session_id)
            except Exception as e:  # noqa: BLE001
                logger.warning("Redis load failed, using local store: %s", e)
        return await self._store.load(session_id)


conversation_memory = ConversationMemory()
