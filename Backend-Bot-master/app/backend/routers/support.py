import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import and_, case, delete, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.backend.deps import require_role
from app.config import MAX_SUPPORT_ENTRY_TTL_SECONDS, MAX_SUPPORT_LANDING_LINKS_PER_MINUTE, SUPPORT_INTERNAL_TOKEN
from app.enum import RoleCode
from app.models import SupportConversation, SupportEntryToken, SupportMessage, SupportMessageAttachment, User
from app.schemas.support import (
    LandingSupportLinkCreate,
    MaxLinkResponse,
    SupportCloseResponse,
    SupportConversationDetail,
    SupportConversationList,
    SupportConversationSummary,
    SupportMessageCreate,
    SupportMessageResponse,
    SupportReadCreate,
    SupportReadResponse,
    SupportUnreadCount,
)
from app.services.max_bot import MaxIncomingEvent, MaxNotConfiguredError, max_bot_service

support_router = APIRouter()
_landing_link_requests: dict[str, deque[float]] = defaultdict(deque)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _create_support_link(request: Request, source: str, user_id: int | None, metadata: dict[str, Any] | None = None) -> MaxLinkResponse:
    raw_token = secrets.token_urlsafe(24)
    expires_at = _now() + timedelta(seconds=MAX_SUPPORT_ENTRY_TTL_SECONDS)
    try:
        url = max_bot_service.build_support_link(raw_token)
    except MaxNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    request.state.session.add(
        SupportEntryToken(
            token_hash=_token_hash(raw_token),
            user_id=user_id,
            source=source,
            entry_metadata=metadata,
            expires_at=expires_at,
        )
    )
    await request.state.session.commit()
    return MaxLinkResponse(url=url, expires_at=expires_at, source=source)


@support_router.post("/support/max-link", response_model=MaxLinkResponse)
async def max_link(request: Request, user: User = Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))):
    return await _create_support_link(request, "APP", user.id)


@support_router.post("/support/landing/max-link", response_model=MaxLinkResponse)
async def landing_max_link(request: Request, body: LandingSupportLinkCreate):
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    client_key = forwarded_for or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    requests = _landing_link_requests[client_key]
    while requests and requests[0] <= now - 60:
        requests.popleft()
    if len(requests) >= MAX_SUPPORT_LANDING_LINKS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many support link requests")
    requests.append(now)
    await request.state.session.execute(
        delete(SupportEntryToken).where(
            SupportEntryToken.expires_at < _now() - timedelta(days=1),
        )
    )
    metadata = {"campaign": body.campaign} if body.campaign else None
    return await _create_support_link(request, "LANDING", None, metadata)


async def _consume_entry_token(session, event: MaxIncomingEvent) -> SupportEntryToken | None:
    if not event.start_payload:
        return None
    token = await session.scalar(
        select(SupportEntryToken)
        .where(
            SupportEntryToken.token_hash == _token_hash(event.start_payload),
            SupportEntryToken.consumed_at.is_(None),
            SupportEntryToken.expires_at > _now(),
        )
        .with_for_update()
    )
    if token is None:
        return None
    token.consumed_at = _now()
    token.consumed_max_user_id = event.user_id
    token.consumed_max_chat_id = event.chat_id
    return token


def _attachment_values(raw: dict[str, Any]) -> dict[str, Any]:
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    file_name = payload.get("name") or payload.get("file_name") or payload.get("filename")
    url = payload.get("url") or payload.get("photo_url") or payload.get("download_url")
    size = payload.get("size")
    return {
        "attachment_type": str(raw.get("type") or "file")[:30],
        "file_name": str(file_name)[:500] if file_name is not None else None,
        "mime_type": str(payload.get("mime_type"))[:255] if payload.get("mime_type") is not None else None,
        "file_size": int(size) if isinstance(size, (int, float)) and size >= 0 else None,
        "provider_url": str(url) if url is not None else None,
        "provider_metadata": payload,
    }


async def _get_or_create_open_conversation(session, event: MaxIncomingEvent, token: SupportEntryToken | None) -> tuple[SupportConversation, bool]:
    conversation = await session.scalar(
        select(SupportConversation)
        .where(SupportConversation.max_chat_id == event.chat_id, SupportConversation.status == "OPEN")
        .with_for_update()
    )
    first_event = conversation is None
    if conversation is None:
        conversation = SupportConversation(
            max_chat_id=event.chat_id,
            max_user_id=event.user_id,
            user_id=token.user_id if token else None,
            source=token.source if token else "DIRECT",
            status="OPEN",
        )
        try:
            async with session.begin_nested():
                session.add(conversation)
                await session.flush()
        except IntegrityError:
            conversation = await session.scalar(
                select(SupportConversation).where(
                    SupportConversation.max_chat_id == event.chat_id,
                    SupportConversation.status == "OPEN",
                )
            )
            if conversation is None:
                raise
            first_event = False
    if token is not None:
        conversation.user_id = token.user_id
        conversation.source = token.source
    if event.user_id is not None and conversation.max_user_id is None:
        conversation.max_user_id = event.user_id
    conversation.updated_at = _now()
    return conversation, first_event


@support_router.post("/integrations/max/webhook", status_code=200)
async def max_webhook(
    request: Request,
    body: dict,
    x_max_bot_api_secret: str | None = Header(None, alias="X-Max-Bot-Api-Secret"),
):
    if not max_bot_service.verify_webhook_secret(x_max_bot_api_secret):
        raise HTTPException(status_code=403, detail="Invalid MAX webhook secret")
    event = max_bot_service.parse_incoming_event(body)
    if event is None or event.sender_is_bot or (event.chat_type is not None and event.chat_type.lower() not in {"dialog", "private"}):
        return {"status": "ignored"}

    session = request.state.session
    if event.external_message_id:
        duplicate = await session.scalar(select(SupportMessage).where(SupportMessage.external_message_id == event.external_message_id))
        if duplicate:
            return {"status": "duplicate", "conversation_id": duplicate.conversation_id}

    token = await _consume_entry_token(session, event)
    conversation, first_event = await _get_or_create_open_conversation(session, event, token)
    incoming_message = None
    if event.text is not None or event.attachments:
        incoming_message = SupportMessage(
            conversation_id=conversation.id,
            sender_type="USER",
            text=event.text,
            external_message_id=event.external_message_id,
            message_type="ATTACHMENT" if event.attachments else "TEXT",
            delivery_status="RECEIVED",
            attachments=[],
        )
        try:
            async with session.begin_nested():
                session.add(incoming_message)
                await session.flush()
        except IntegrityError:
            duplicate = await session.scalar(select(SupportMessage).where(SupportMessage.external_message_id == event.external_message_id))
            if duplicate:
                return {"status": "duplicate", "conversation_id": duplicate.conversation_id}
            raise
        for attachment in event.attachments:
            session.add(SupportMessageAttachment(message_id=incoming_message.id, **_attachment_values(attachment)))
        conversation.last_inbound_message_id = incoming_message.id
        conversation.last_inbound_at = _now()
    await session.commit()

    if first_event:
        greeting = "Здравствуйте! Ваше обращение принято. Оператор ответит вам здесь."
        try:
            external_id = await max_bot_service.send_message(event.chat_id, greeting)
        except Exception:
            pass
        else:
            bot_message = SupportMessage(
                conversation_id=conversation.id,
                sender_type="BOT",
                text=greeting,
                external_message_id=external_id,
                delivery_status="SENT",
            )
            session.add(bot_message)
            conversation.last_outbound_at = _now()
            conversation.updated_at = _now()
            await session.commit()
    return {"status": "accepted", "conversation_id": conversation.id}


def _message_options():
    return selectinload(SupportConversation.messages).selectinload(SupportMessage.attachments)


def _unread_count_expression():
    return func.count(
        case(
            (
                and_(
                    SupportMessage.sender_type == "USER",
                    SupportMessage.id > func.coalesce(SupportConversation.last_read_message_id, 0),
                ),
                1,
            )
        )
    )


def _summary(conversation: SupportConversation, unread_count: int = 0) -> SupportConversationSummary:
    messages = list(conversation.messages)
    latest = max(messages, key=lambda item: (item.created_at, item.id)) if messages else None
    user = conversation.user
    display_name = None
    phone = None
    if user is not None:
        display_name = " ".join(filter(None, (user.first_name, user.last_name))) or None
        phone = user.phone
    return SupportConversationSummary.model_validate(
        {
            **conversation.__dict__,
            "latest_message": latest,
            "unread_count": unread_count,
            "has_unread": unread_count > 0,
            "display_name": display_name,
            "phone": phone,
        }
    )


@support_router.get("/admin/support/conversations", response_model=SupportConversationList, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def list_conversations(
    request: Request,
    status: str | None = Query(None),
    unread: bool | None = Query(None),
    source: str | None = Query(None),
    q: str | None = Query(None, max_length=100),
    cursor: int | None = Query(None, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    unread_count = _unread_count_expression().label("unread_count")
    query = (
        select(SupportConversation, unread_count)
        .outerjoin(SupportMessage, SupportMessage.conversation_id == SupportConversation.id)
        .options(_message_options(), selectinload(SupportConversation.user))
        .group_by(SupportConversation.id)
        .order_by(desc(SupportConversation.id))
        .limit(page_size + 1)
    )
    if status:
        query = query.where(SupportConversation.status == status.upper())
    if source:
        query = query.where(SupportConversation.source == source.upper())
    if cursor:
        query = query.where(SupportConversation.id < cursor)
    if q:
        numeric = int(q.lstrip("#")) if q.lstrip("#").isdigit() else None
        conditions = [SupportConversation.user.has(or_(User.phone.ilike(f"%{q}%"), User.first_name.ilike(f"%{q}%"), User.last_name.ilike(f"%{q}%")))]
        if numeric is not None:
            conditions.extend((SupportConversation.id == numeric, SupportConversation.max_user_id == numeric))
        query = query.where(or_(*conditions))
    if unread is True:
        query = query.having(unread_count > 0)
    elif unread is False:
        query = query.having(unread_count == 0)
    rows = (await request.state.session.execute(query)).all()
    has_more = len(rows) > page_size
    rows = rows[:page_size]
    return SupportConversationList(
        items=[_summary(conversation, count) for conversation, count in rows],
        next_cursor=rows[-1][0].id if has_more and rows else None,
    )


async def _conversation_or_404(request: Request, conversation_id: int) -> SupportConversation:
    conversation = await request.state.session.scalar(
        select(SupportConversation)
        .options(_message_options(), selectinload(SupportConversation.user))
        .where(SupportConversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    return conversation


@support_router.get("/admin/support/conversations/{conversation_id}", response_model=SupportConversationDetail, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def conversation_detail(request: Request, conversation_id: int):
    conversation = await _conversation_or_404(request, conversation_id)
    unread_count = sum(
        message.sender_type == "USER" and message.id > (conversation.last_read_message_id or 0)
        for message in conversation.messages
    )
    summary = _summary(conversation, unread_count)
    return SupportConversationDetail.model_validate(
        {**summary.model_dump(), "messages": sorted(conversation.messages, key=lambda item: (item.created_at, item.id))}
    )


async def _send_operator_message(session, conversation: SupportConversation, body: SupportMessageCreate, operator_name: str, user_id: int | None) -> SupportMessage:
    existing = await session.scalar(
        select(SupportMessage)
        .options(selectinload(SupportMessage.attachments))
        .where(
            SupportMessage.conversation_id == conversation.id,
            SupportMessage.idempotency_key == body.idempotency_key,
        )
    )
    if existing and existing.delivery_status != "FAILED":
        return existing
    if conversation.status != "OPEN":
        raise HTTPException(status_code=409, detail="Conversation is closed")
    if existing:
        message = existing
        message.delivery_status = "PENDING"
        message.delivery_error = None
    else:
        message = SupportMessage(
            conversation_id=conversation.id,
            sender_type="OPERATOR",
            user_id=user_id,
            operator_name=operator_name,
            text=body.text.strip(),
            idempotency_key=body.idempotency_key,
            delivery_status="PENDING",
            attachments=[],
        )
        try:
            async with session.begin_nested():
                session.add(message)
                await session.flush()
        except IntegrityError:
            message = await session.scalar(
                select(SupportMessage)
                .options(selectinload(SupportMessage.attachments))
                .where(
                    SupportMessage.conversation_id == conversation.id,
                    SupportMessage.idempotency_key == body.idempotency_key,
                )
            )
            if message is None or message.delivery_status != "FAILED":
                return message
            message.delivery_status = "PENDING"
            message.delivery_error = None
    conversation.updated_at = _now()
    await session.commit()
    try:
        external_id = await max_bot_service.send_message(conversation.max_chat_id, message.text)
    except Exception as exc:
        message.delivery_status = "FAILED"
        message.delivery_error = str(exc)[:500]
        await session.commit()
        return message
    message.delivery_status = "SENT"
    message.external_message_id = external_id
    message.delivery_error = None
    conversation.last_outbound_at = _now()
    conversation.updated_at = _now()
    await session.commit()
    return message


@support_router.post("/admin/support/conversations/{conversation_id}/messages", response_model=SupportMessageResponse)
async def operator_message(request: Request, conversation_id: int, body: SupportMessageCreate, admin: User = Depends(require_role(RoleCode.ADMIN))):
    conversation = await request.state.session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    name = " ".join(filter(None, (admin.first_name, admin.last_name))) or f"admin:{admin.id}"
    return await _send_operator_message(request.state.session, conversation, body, name, admin.id)


async def _mark_read(request: Request, conversation_id: int, body: SupportReadCreate) -> SupportReadResponse:
    conversation = await request.state.session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    marker = await request.state.session.scalar(
        select(SupportMessage.id).where(
            SupportMessage.id == body.up_to_message_id,
            SupportMessage.conversation_id == conversation_id,
            SupportMessage.sender_type == "USER",
        )
    )
    if marker is None:
        raise HTTPException(status_code=400, detail="Read marker must reference an inbound message in this conversation")
    if body.up_to_message_id > (conversation.last_read_message_id or 0):
        conversation.last_read_message_id = body.up_to_message_id
        await request.state.session.commit()
    unread_count = await request.state.session.scalar(
        select(func.count(SupportMessage.id)).where(
            SupportMessage.conversation_id == conversation_id,
            SupportMessage.sender_type == "USER",
            SupportMessage.id > (conversation.last_read_message_id or 0),
        )
    )
    return SupportReadResponse(id=conversation.id, last_read_message_id=conversation.last_read_message_id, unread_count=unread_count or 0)


@support_router.post("/admin/support/conversations/{conversation_id}/read", response_model=SupportReadResponse, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def mark_read(request: Request, conversation_id: int, body: SupportReadCreate):
    return await _mark_read(request, conversation_id, body)


@support_router.get("/admin/support/unread-count", response_model=SupportUnreadCount, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def unread_count(request: Request):
    unread_filter = and_(
        SupportMessage.sender_type == "USER",
        SupportMessage.id > func.coalesce(SupportConversation.last_read_message_id, 0),
    )
    row = (
        await request.state.session.execute(
            select(func.count(SupportMessage.id), func.count(func.distinct(SupportConversation.id)))
            .select_from(SupportConversation)
            .join(SupportMessage, SupportMessage.conversation_id == SupportConversation.id)
            .where(unread_filter)
        )
    ).one()
    return SupportUnreadCount(unread_messages=row[0], unread_conversations=row[1])


async def _set_status(request: Request, conversation_id: int, status: str, operator_name: str | None = None) -> SupportCloseResponse:
    conversation = await request.state.session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    if status == "OPEN":
        active = await request.state.session.scalar(
            select(SupportConversation).where(
                SupportConversation.max_chat_id == conversation.max_chat_id,
                SupportConversation.status == "OPEN",
                SupportConversation.id != conversation.id,
            )
        )
        if active:
            raise HTTPException(status_code=409, detail=f"Active conversation: {active.id}")
        conversation.closed_at = None
        conversation.closed_by = None
    else:
        conversation.closed_at = _now()
        conversation.closed_by = operator_name
    conversation.status = status
    conversation.updated_at = _now()
    await request.state.session.commit()
    return SupportCloseResponse(id=conversation.id, status=conversation.status)


@support_router.post("/admin/support/conversations/{conversation_id}/close", response_model=SupportCloseResponse)
async def close_conversation(request: Request, conversation_id: int, admin: User = Depends(require_role(RoleCode.ADMIN))):
    return await _set_status(request, conversation_id, "CLOSED", f"admin:{admin.id}")


@support_router.post("/admin/support/conversations/{conversation_id}/reopen", response_model=SupportCloseResponse, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def reopen_conversation(request: Request, conversation_id: int):
    return await _set_status(request, conversation_id, "OPEN")


def _require_internal(supplied: str | None) -> None:
    if not SUPPORT_INTERNAL_TOKEN or not supplied or not hmac.compare_digest(SUPPORT_INTERNAL_TOKEN, supplied):
        raise HTTPException(status_code=403, detail="Invalid support internal token")


@support_router.post("/internal/support/conversations/{conversation_id}/messages", response_model=SupportMessageResponse)
async def internal_operator_message(
    request: Request,
    conversation_id: int,
    body: SupportMessageCreate,
    x_support_internal_token: str | None = Header(None, alias="X-Support-Internal-Token"),
    x_support_operator: str = Header("operator", alias="X-Support-Operator"),
):
    _require_internal(x_support_internal_token)
    conversation = await request.state.session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    return await _send_operator_message(request.state.session, conversation, body, x_support_operator[:150], None)


@support_router.post("/internal/support/conversations/{conversation_id}/read", response_model=SupportReadResponse)
async def internal_mark_read(request: Request, conversation_id: int, body: SupportReadCreate, x_support_internal_token: str | None = Header(None, alias="X-Support-Internal-Token")):
    _require_internal(x_support_internal_token)
    return await _mark_read(request, conversation_id, body)


@support_router.post("/internal/support/conversations/{conversation_id}/{action}", response_model=SupportCloseResponse)
async def internal_status(
    request: Request,
    conversation_id: int,
    action: str,
    x_support_internal_token: str | None = Header(None, alias="X-Support-Internal-Token"),
    x_support_operator: str = Header("operator", alias="X-Support-Operator"),
):
    _require_internal(x_support_internal_token)
    if action not in {"close", "reopen"}:
        raise HTTPException(status_code=404, detail="Unknown support action")
    return await _set_status(request, conversation_id, "CLOSED" if action == "close" else "OPEN", x_support_operator[:150])
