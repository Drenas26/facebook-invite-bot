import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

# Проверка наличия обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env")
if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY не найден в .env")
    
# Новые настройки: 3 проверки с интервалом 7 секунд
CHECK_ATTEMPTS = 3  # количество попыток
CHECK_INTERVAL = 7   # интервал между попытками (секунды)

