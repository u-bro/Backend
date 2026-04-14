import os, sys
from pathlib import Path
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent

if 'pytest' in sys.modules:
    load_dotenv(dotenv_path='.env-test', override=True)
else:
    load_dotenv()


DB_HOST = os.environ.get('DB_HOST') or os.getenv('DB_HOST')
DB_PORT = os.environ.get('DB_PORT') or os.getenv('DB_PORT')
DB_NAME = os.environ.get('DB_NAME') or os.getenv('DB_NAME')
DB_USER = os.environ.get('DB_USER') or os.getenv('DB_USER')
DB_PASS = os.environ.get('DB_PASS') or os.getenv('DB_PASS')

API_IGNORE = ['/docs', '/openapi.json', '']
ENABLE_PUBLIC_API_DOCS = os.getenv('ENABLE_PUBLIC_API_DOCS', '0') in {'1', 'true', 'True', 'yes', 'YES'}

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SMSAERO_EMAIL = os.environ.get('SMSAERO_EMAIL') or 'test-smsaero-email'
SMSAERO_API_KEY = os.environ.get('SMSAERO_API_KEY') or 'test-smsaero-api-key'
ENABLE_SMSAERO = os.environ.get('ENABLE_SMSAERO')
OTP_TTL = int(os.environ.get('OTP_TTL', 120))
OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', 3))
OTP_NEXT_SENDING_SECONDS = int(os.environ.get('OTP_NEXT_SENDING_SECONDS', 30))

MAX_DISTANCE_KM = float(os.environ.get('MAX_DISTANCE_KM', 5.0))
FEED_PUSH_INTERVAL_SECONDS = int(os.getenv("MATCHING_FEED_PUSH_INTERVAL_SECONDS", "5"))
DRIVER_LOCATION_PUSH_INTERVAL_SECONDS = int(os.getenv("DRIVER_LOCATION_PUSH_INTERVAL_SECONDS", "5"))
FEED_LIMIT = int(os.getenv("MATCHING_FEED_LIMIT", "20"))
COMMISSION_PAY_SECONDS_LIMIT = int(os.getenv("COMMISSION_PAY_SECONDS_LIMIT", "300"))
RIDE_SECONDS_LIMIT = int(os.getenv("RIDE_SECONDS_LIMIT", "3600"))
RATING_AVG_COUNT = int(os.getenv("RATING_AVG_COUNT", "5"))

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'test-secret-key'
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM') or 'HS256'
JWT_EXPIRATION_MINUTES = int(os.environ.get('JWT_EXPIRATION_MINUTES', 15))

REFRESH_TOKEN_EXPIRATION_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRATION_DAYS', 7))
REFRESH_TOKEN_SALT = os.environ.get('REFRESH_TOKEN_SALT') or 'test-refresh-token-salt'

S3_DOCUMENTS_BUCKET = os.environ.get('S3_DOCUMENTS_BUCKET') or 'ubro-documents'
S3_AVATARS_BUCKET = os.environ.get('S3_AVATARS_BUCKET') or 'ubro-avatar'
S3_AVATARS_BUCKET_UUID = os.environ.get('S3_AVATARS_BUCKET_UUID') or 'ubro-avatar-uuid'
AWS_ACCESS_KEY_ID=os.environ.get('AWS_ACCESS_KEY_ID') or 'test-aws-access-key-id'
AWS_SECRET_KEY=os.environ.get('AWS_SECRET_KEY') or 'test-aws-secret-access-key'

FIREBASE_SERVICE_ACCOUNT_PATH=os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH') or 'firebase-service-account.json'

TBANK_USE_SANDBOX = (os.getenv("TBANK_USE_SANDBOX", os.getenv("TOCHKA_USE_SANDBOX", "false")).lower() in ("1", "true", "yes"))
TBANK_BASE_URL = os.getenv("TBANK_BASE_URL", "https://securepay.tinkoff.ru/v2/")
TBANK_SANDBOX_URL = os.getenv("TBANK_SANDBOX_URL", os.getenv("TBANK_BASE_URL", "https://securepay.tinkoff.ru/v2/"))
TBANK_TERMINAL_KEY = os.getenv("TBANK_TERMINAL_KEY")
TBANK_TERMINAL_PASSWORD = os.getenv("TBANK_TERMINAL_PASSWORD")
TBANK_PAYMENT_REDIRECT_URL = os.getenv("TBANK_PAYMENT_REDIRECT_URL", os.getenv("TOCHKA_ACQUIRING_REDIRECT_URL"))
TBANK_PAYMENT_FAIL_REDIRECT_URL = os.getenv("TBANK_PAYMENT_FAIL_REDIRECT_URL", os.getenv("TOCHKA_ACQUIRING_FAIL_REDIRECT_URL"))
TBANK_PAYMENT_NOTIFICATION_URL = os.getenv("TBANK_PAYMENT_NOTIFICATION_URL")
TBANK_WEBHOOK_EXAMPLE = os.getenv("TBANK_WEBHOOK_EXAMPLE", os.getenv("TOCHKA_WEBHOOK_EXAMPLE"))
