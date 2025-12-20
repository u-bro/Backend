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

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'test-secret-key'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24