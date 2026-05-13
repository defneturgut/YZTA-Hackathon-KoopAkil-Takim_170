"""Chat endpoints — REST + WebSocket.

Strategy:
- REST ``POST /chat/message`` runs the RAG + agent pipeline and returns
  a single response. Best for the demo flow.
- ``GET /chat/conversations`` lists persisted sessions.
- ``WebSocket /chat/ws`` lets the frontend stream user messages and
  receive structured response events without polling.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.agents import operations_agent
from app.ai.memory.conversation_memory import conversation_memory
from app.ai.prompts import load_prompt
from app.ai.rag.pipeline import generate_grounded_answer
from app.database import AsyncSessionLocal, get_db
from app.models.conversation import Conversation, Message, MessageRole
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    ConversationRead,
)

logger = logging.getLogger("aegis.api.chat")
router = APIRouter()


# -------------------------------------------------------------------------
# REST: single-shot chat
# -------------------------------------------------------------------------
@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Tek atışlık chat endpoint.

    Her durumda 200 ve `ChatResponse` döner — herhangi bir alt katman
    patlarsa kullanıcıya boş ekran yerine açıklayıcı bir hata mesajı
    iletilir. Tüm aşamalar `aegis.api.chat` logger'ında izlenebilir.
    """
    session_id = payload.session_id or _new_session_id()
    logger.info("chat.start session=%s msg=%r", session_id, payload.message[:80])

    # Persist user turn — bu adım hata verirse bile devam et.
    try:
        convo = await _get_or_create_conversation(db, session_id, payload.channel)
        await _append_message(db, convo.id, MessageRole.USER, payload.message)
        await conversation_memory.append(session_id, "user", payload.message)
    except Exception:  # noqa: BLE001
        logger.exception("chat.persist_user_turn_failed session=%s", session_id)
        convo = None  # type: ignore[assignment]

    text: str = ""
    sources: List[ChatSource] = []
    tool_calls: list = []
    confidence: float = 0.5
    latency_ms: int = 0
    model: str = "unknown"
    error_message: str | None = None

    try:
        history = await conversation_memory.load(session_id)
        is_op = _is_operational(payload.message)
        logger.info(
            "chat.route session=%s intent=%s", session_id, "operational" if is_op else "support"
        )

        if is_op:
            agent_result = await operations_agent.run(payload.message, db)
            text = agent_result["message"]
            sources = [
                ChatSource(
                    type="tool",
                    label=call["tool"],
                    reference=call["tool"],
                    excerpt=json.dumps(call.get("result"), ensure_ascii=False)[:240],
                )
                for call in agent_result["tool_calls"]
            ]
            confidence = float(agent_result["confidence"])
            latency_ms = int(agent_result["latency_ms"])
            tool_calls = agent_result["tool_calls"]
            model = agent_result["model"]
        else:
            system_prompt = load_prompt("customer_support") or ""
            response, retrieved = await generate_grounded_answer(
                db,
                payload.message,
                system_prompt=system_prompt,
                history=history,
            )
            text = response.text
            sources = [
                ChatSource(
                    type="document",
                    label=r.document_title,
                    reference=f"doc:{r.document_id}#{r.chunk_index}",
                    excerpt=r.content[:240],
                )
                for r in retrieved
            ]
            confidence = response.confidence
            latency_ms = response.latency_ms
            tool_calls = []
            model = response.model

        logger.info(
            "chat.success session=%s model=%s len=%d latency=%dms",
            session_id,
            model,
            len(text or ""),
            latency_ms,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("chat.failed session=%s", session_id)
        error_message = str(e) or "Bilinmeyen hata"
        text = (
            "⚠️ Yanıt üretirken bir sorunla karşılaştım. Lütfen tekrar deneyin.\n\n"
            f"_Teknik detay: {error_message[:200]}_"
        )
        confidence = 0.0
        model = "error"

    # Persist assistant turn (best-effort).
    if convo is not None:
        try:
            await _append_message(
                db,
                convo.id,
                MessageRole.ASSISTANT,
                text,
                confidence=confidence,
                sources=[s.model_dump() for s in sources],
                tool_calls=tool_calls,
                latency_ms=latency_ms,
            )
            await conversation_memory.append(session_id, "assistant", text)
        except Exception:  # noqa: BLE001
            logger.exception(
                "chat.persist_assistant_turn_failed session=%s", session_id
            )

    return ChatResponse(
        session_id=session_id,
        message=text,
        confidence=confidence,
        sources=sources,
        tool_calls=tool_calls,
        latency_ms=latency_ms,
        model=model,
    )


# -------------------------------------------------------------------------
# REST: conversations + messages
# -------------------------------------------------------------------------
@router.get("/conversations", response_model=List[ConversationRead])
async def list_conversations(db: AsyncSession = Depends(get_db)) -> List[ConversationRead]:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    return [ConversationRead.model_validate(c) for c in result.scalars().all()]


@router.get("/conversations/{session_id}", response_model=ConversationRead)
async def get_conversation(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> ConversationRead:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.session_id == session_id)
    )
    result = await db.execute(stmt)
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı.")
    return ConversationRead.model_validate(convo)


# -------------------------------------------------------------------------
# WebSocket: streaming-style chat
# -------------------------------------------------------------------------
@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id = websocket.query_params.get("session_id") or _new_session_id()
    await websocket.send_json({"event": "session", "session_id": session_id})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                message = payload.get("message", "")
            except json.JSONDecodeError:
                message = raw
            if not message:
                continue

            await websocket.send_json({"event": "thinking"})

            async with AsyncSessionLocal() as db:
                req = ChatRequest(message=message, session_id=session_id, channel="ws")
                response = await send_message(req, db)

            await websocket.send_json({"event": "message", "data": response.model_dump()})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("WebSocket error")
        try:
            await websocket.send_json({"event": "error", "detail": str(e)})
        finally:
            await websocket.close()


# -------------------------------------------------------------------------
# Internals
# -------------------------------------------------------------------------
def _new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:16]}"


def _is_operational(message: str) -> bool:
    """Route operational queries to the agent, support queries to RAG.

    Çok geniş bir liste kullanıyoruz çünkü Türkçe'de "stok" kelimesi
    kullanılmadan da sayısal sorgular yapılabilir:
      - "Defne sabunundan kaç tane var?"
      - "Bal ne kadar kaldı?"
      - "Çay mevcut mu?"
    Bunlar agent'a gitmeli ki inventory_tool gerçek envanter verisini çekebilsin.
    """
    keywords = (
        # Stok / envanter
        "stok", "envanter", "ürün", "mevcut", "kalan", "kaldı", "kala",
        "kaç", "ne kadar", "adet", "var mı", "tükendi", "azaldı", "azalan",
        "kritik", "yetiyor", "yeter", "yenile", "tedarik", "sipariş ver",
        # Kargo / lojistik
        "kargo", "shipment", "teslim", "gönderi", "geciken", "gecikme",
        "takip", "yolda", "transit",
        # Operasyon / yönetim
        "risk", "operasyon", "görev", "rapor", "analiz", "rotalama",
        "günlük plan", "tahmin", "satış",
    )
    return any(k in message.lower() for k in keywords)


async def _get_or_create_conversation(
    db: AsyncSession, session_id: str, channel: str
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.session_id == session_id)
    )
    convo = result.scalar_one_or_none()
    if convo:
        return convo
    convo = Conversation(session_id=session_id, channel=channel, title="Yeni Sohbet")
    db.add(convo)
    await db.commit()
    await db.refresh(convo)
    return convo


async def _append_message(
    db: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str,
    *,
    confidence: float | None = None,
    sources: list | None = None,
    tool_calls: list | None = None,
    latency_ms: int | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        confidence=confidence,
        sources_json=json.dumps(sources, ensure_ascii=False) if sources else None,
        tool_calls_json=(
            json.dumps(tool_calls, default=str, ensure_ascii=False) if tool_calls else None
        ),
        latency_ms=latency_ms,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
