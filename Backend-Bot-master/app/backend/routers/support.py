from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from app.backend.deps import require_role
from app.enum import RoleCode
from app.models import SupportConversation, SupportMessage, User
from app.schemas.support import MaxLinkResponse, MaxWebhookRequest, SupportCloseResponse, SupportConversationDetail, SupportConversationSummary, SupportMessageCreate, SupportMessageResponse
from app.services.max_bot import MaxNotConfiguredError, max_bot_service

support_router = APIRouter()


@support_router.post("/support/max-link", response_model=MaxLinkResponse)
async def max_link(user: User = Depends(require_role([RoleCode.USER, RoleCode.DRIVER, RoleCode.ADMIN]))):
    try:
        return MaxLinkResponse(url=max_bot_service.build_support_link(user.id))
    except MaxNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@support_router.post("/integrations/max/webhook", status_code=202)
async def max_webhook(request: Request, body: MaxWebhookRequest, x_max_webhook_secret: str | None = Header(None)):
    if not max_bot_service.verify_webhook_secret(x_max_webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid MAX webhook secret")
    event = max_bot_service.parse_incoming_event(body.model_dump(exclude_none=True))
    if event is None:
        raise HTTPException(status_code=400, detail="Unsupported MAX webhook event")
    session = request.state.session
    if event.external_message_id:
        duplicate = await session.scalar(select(SupportMessage).where(SupportMessage.external_message_id == event.external_message_id))
        if duplicate:
            return {"status": "duplicate", "conversation_id": duplicate.conversation_id}
    conversation = await session.scalar(select(SupportConversation).where(SupportConversation.max_chat_id == event.chat_id, SupportConversation.status == "OPEN"))
    first_message = conversation is None
    if conversation is None:
        conversation = SupportConversation(max_chat_id=event.chat_id, max_user_id=event.user_id, status="OPEN")
        session.add(conversation)
        await session.flush()
    elif event.user_id is not None and conversation.max_user_id is None:
        conversation.max_user_id = event.user_id
    conversation.updated_at = datetime.now(timezone.utc)
    session.add(SupportMessage(conversation_id=conversation.id, sender_type="USER", user_id=None, text=event.text, external_message_id=event.external_message_id))
    # A greeting is deliberately sent only through the adapter; persistence is independent of transport availability.
    await session.commit()
    if first_message:
        greeting = "Здравствуйте! Ваше обращение принято. Оператор ответит вам здесь."
        try:
            await max_bot_service.send_message(event.chat_id, greeting)
        except Exception:
            # The provider adapter is optional; the incoming message remains persisted.
            pass
        else:
            session.add(SupportMessage(conversation_id=conversation.id, sender_type="BOT", text=greeting))
            conversation.updated_at = datetime.now(timezone.utc)
            await session.commit()
    return {"status": "accepted", "conversation_id": conversation.id}


def _message_response(message: SupportMessage) -> SupportMessageResponse:
    return SupportMessageResponse.model_validate(message)


@support_router.get("/admin/support/conversations", response_model=list[SupportConversationSummary], dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def list_conversations(request: Request, status: str | None = Query(None), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    session = request.state.session
    query = (select(SupportConversation)
             .outerjoin(SupportMessage, SupportMessage.conversation_id == SupportConversation.id)
             .options(selectinload(SupportConversation.messages))
             .group_by(SupportConversation.id)
             .order_by(desc(func.max(SupportMessage.created_at)), desc(SupportConversation.id))
             .offset((page - 1) * page_size).limit(page_size))
    if status:
        query = query.where(SupportConversation.status == status.upper())
    conversations = (await session.scalars(query)).all()
    return [SupportConversationSummary.model_validate({**c.__dict__, "latest_message": max(c.messages, key=lambda m: m.created_at) if c.messages else None}) for c in conversations]


@support_router.get("/admin/support/conversations/{conversation_id}", response_model=SupportConversationDetail, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def conversation_detail(request: Request, conversation_id: int):
    conversation = await request.state.session.scalar(select(SupportConversation).options(selectinload(SupportConversation.messages)).where(SupportConversation.id == conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    return SupportConversationDetail.model_validate({**conversation.__dict__, "messages": conversation.messages, "latest_message": max(conversation.messages, key=lambda m: m.created_at) if conversation.messages else None})


@support_router.post("/admin/support/conversations/{conversation_id}/messages", response_model=SupportMessageResponse, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def operator_message(request: Request, conversation_id: int, body: SupportMessageCreate, admin: User = Depends(require_role(RoleCode.ADMIN))):
    session = request.state.session
    conversation = await session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    message = SupportMessage(conversation_id=conversation_id, sender_type="OPERATOR", user_id=admin.id, text=body.text)
    session.add(message)
    conversation.updated_at = datetime.now(timezone.utc)
    await session.commit()
    try:
        await max_bot_service.send_message(conversation.max_chat_id, body.text)
    except MaxNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=f"Message saved but not delivered: {exc}")
    except Exception:
        raise HTTPException(status_code=502, detail="Message saved but MAX delivery failed")
    return message


async def _set_status(request: Request, conversation_id: int, status: str) -> SupportCloseResponse:
    conversation = await request.state.session.get(SupportConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Support conversation not found")
    conversation.status = status
    await request.state.session.commit()
    return SupportCloseResponse(id=conversation.id, status=conversation.status)


@support_router.post("/admin/support/conversations/{conversation_id}/close", response_model=SupportCloseResponse, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def close_conversation(request: Request, conversation_id: int):
    return await _set_status(request, conversation_id, "CLOSED")


@support_router.post("/admin/support/conversations/{conversation_id}/reopen", response_model=SupportCloseResponse, dependencies=[Depends(require_role(RoleCode.ADMIN))])
async def reopen_conversation(request: Request, conversation_id: int):
    return await _set_status(request, conversation_id, "OPEN")
