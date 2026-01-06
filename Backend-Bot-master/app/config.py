import os
from pathlib import Path
import sys
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

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

TELEGRAM_OTP_BASE_URL = 'https://gatewayapi.telegram.org/'
TELEGRAM_OTP_TOKEN = 'AAEDMAAATZrglNKgaX0kPyOE5krqBpx-M09H3bJM7Q-AdA'

MAX_DISTANCE_KM = float(os.environ.get('MAX_DISTANCE_KM', 5.0))

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'test-secret-key'
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM') or 'HS256'
JWT_EXPIRATION_MINTUES = int(os.environ.get('JWT_EXPIRATION_MINTUES', 15))

REFRESH_TOKEN_EXPIRATION_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRATION_DAYS', 7))
REFRESH_TOKEN_SALT = os.environ.get('REFRESH_TOKEN_SALT') or 'test-refresh-token-salt'

S3_DOCUMENTS_BUCKET=os.environ.get('S3_DOCUMENTS_BUCKET') or 'ubro-documents'
AWS_REGION=os.environ.get('AWS_REGION') or 'ru-central1'
AWS_ACCESS_KEY=os.environ.get('AWS_ACCESS_KEY') or 'test-aws-access-key-id'
AWS_SECRET_KEY=os.environ.get('AWS_SECRET_KEY') or 'test-aws-secret-access-key'