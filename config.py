import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
MAX_WAIT_TIME = int(os.getenv("MAX_WAIT_TIME", 300))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 10))

# Проверка наличия обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env")
if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY не найден в .env")