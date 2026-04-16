import asyncio, json, firebase_admin
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union
from firebase_admin import credentials, messaging
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import FIREBASE_SERVICE_ACCOUNT_PATH, ROOT_DIR
from app.logger import logger
from app.schemas.push import PushSendToTokenRequest, PushSendToTopicRequest, PushSendToUserRequest
from app.crud.device_token import device_token_crud


class FCMService:
    def __init__(self) -> None:
        self._initialized: bool = False
        self._init_lock = asyncio.Lock()

    def _service_account_file(self) -> Path:
        p = Path(FIREBASE_SERVICE_ACCOUNT_PATH)
        if not p.is_absolute():
            p = ROOT_DIR / p
        return p

    def _normalize_data(self, data: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if not data:
            return {}

        normalized: Dict[str, str] = {}
        for k, v in data.items():
            if v is None:
                continue
            if isinstance(v, str):
                normalized[k] = v
            elif isinstance(v, (dict, list, tuple)):
                normalized[k] = json.dumps(v, ensure_ascii=False)
            else:
                normalized[k] = str(v)
        return normalized

    def _build_data_payload(self, payload: Union[PushSendToUserRequest, PushSendToTokenRequest, PushSendToTopicRequest]) -> Dict[str, str]:
        base: Dict[str, Any] = dict(payload.data or {})
        if payload.title is not None:
            base["title"] = payload.title
        if payload.body is not None:
            base["body"] = payload.body
        if payload.image is not None:
            base["image"] = payload.image
        if payload.data is not None:
            base["data"] = payload.data
        return self._normalize_data(base)

    def _build_notification(self, payload: Union[PushSendToUserRequest, PushSendToTokenRequest, PushSendToTopicRequest]) -> messaging.Notification | None:
        if payload.title is None and payload.body is None and payload.image is None:
            return None

        return messaging.Notification(
            title=payload.title,
            body=payload.body,
            image=payload.image,
        )

    def _build_apns_config(self, payload: Union[PushSendToUserRequest, PushSendToTokenRequest, PushSendToTopicRequest]) -> messaging.APNSConfig | None:
        notification = self._build_notification(payload)
        if notification is None:
            return None

        alert = messaging.ApsAlert(
            title=payload.title,
            body=payload.body,
        )
        aps = messaging.Aps(
            alert=alert,
            sound="default",
            mutable_content=bool(payload.image),
        )

        return messaging.APNSConfig(
            headers={
                "apns-push-type": "alert",
                "apns-priority": "10",
            },
            payload=messaging.APNSPayload(aps=aps),
            fcm_options=messaging.APNSFCMOptions(
                image=payload.image,
            ) if payload.image else None,
        )

    async def initialize(self) -> None:
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            key_path = self._service_account_file()
            if not key_path.exists():
                raise FileNotFoundError(f"Firebase service account file not found: {key_path}")

            if firebase_admin._apps:
                self._initialized = True
                return

            cred = credentials.Certificate(str(key_path))
            firebase_admin.initialize_app(cred)
            self._initialized = True
            logger.info("Firebase Admin SDK initialized")

    async def send_to_token(self, payload: PushSendToTokenRequest) -> str:
        await self.initialize()

        message = messaging.Message(
            token=payload.token,
            data=self._build_data_payload(payload),
            notification=self._build_notification(payload),
            apns=self._build_apns_config(payload),
        )

        return await asyncio.to_thread(messaging.send, message)

    async def send_to_tokens(self, tokens: Iterable[str], payload: Union[PushSendToUserRequest, PushSendToTokenRequest, PushSendToTopicRequest], dry_run: bool = False) -> messaging.BatchResponse:
        await self.initialize()

        tokens_list = [t for t in tokens if t]
        if not tokens_list:
            raise ValueError("tokens is empty")

        message = messaging.MulticastMessage(
            tokens=tokens_list,
            data=self._build_data_payload(payload),
            notification=self._build_notification(payload),
            apns=self._build_apns_config(payload),
        )

        return await asyncio.to_thread(messaging.send_each_for_multicast, message, dry_run)

    async def send_to_user(self, session: AsyncSession, user_id: int, payload: Union[PushSendToUserRequest, PushSendToTokenRequest, PushSendToTopicRequest]) -> messaging.BatchResponse | None:
        tokens = await device_token_crud.get_by_user_id(session, user_id)
        token_values = [t.token for t in tokens]
        if not token_values:
            return None
        
        result = None
        try:
            result = await self.send_to_tokens(token_values, payload)
        except Exception as e:
            logger.error(f"Error sending push notification to user {user_id}: {e}")
        
        return result

    async def send_to_topic(self, payload: PushSendToTopicRequest) -> str:
        await self.initialize()

        message = messaging.Message(
            topic=payload.topic,
            data=self._build_data_payload(payload),
            notification=self._build_notification(payload),
            apns=self._build_apns_config(payload),
        )

        return await asyncio.to_thread(messaging.send, message)

    async def subscribe_to_topic(self, tokens: Iterable[str], topic: str) -> messaging.TopicManagementResponse:
        await self.initialize()
        tokens_list = [t for t in tokens if t]
        if not tokens_list:
            raise ValueError("tokens is empty")
        return await asyncio.to_thread(messaging.subscribe_to_topic, tokens_list, topic)

    async def unsubscribe_from_topic(self, tokens: Iterable[str], topic: str) -> messaging.TopicManagementResponse:
        await self.initialize()
        tokens_list = [t for t in tokens if t]
        if not tokens_list:
            raise ValueError("tokens is empty")
        return await asyncio.to_thread(messaging.unsubscribe_from_topic, tokens_list, topic)


fcm_service = FCMService()
