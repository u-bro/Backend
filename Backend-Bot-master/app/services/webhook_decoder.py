import jwt, json
from jwt import exceptions, PyJWK
from fastapi import HTTPException
from app.logger import logger
from app.config import TOCHKA_WEBHOOK_OPEN_KEY


class WebhookDecoder:

    def __init__(self, key_json: str):
        key = json.loads(key_json)
        self.jwk_key = PyJWK(key)
    
    def decode_tochka_webhook(self, payload: str):
        try:
            webhook_jwt = jwt.decode(
                payload,
                self.jwk_key.key,
                algorithms=["RS256"],
            )
        except exceptions.DecodeError:
            raise HTTPException(status_code=403, detail="Forbidden")
        except Exception as e:
            logger.error(f"Error decoding Tochka webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

        return webhook_jwt

webhook_decoder = WebhookDecoder(TOCHKA_WEBHOOK_OPEN_KEY)
