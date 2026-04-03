import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Gmailnator
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

# Firstmail
FIRSTMAIL_API_KEY = os.getenv("FIRSTMAIL_API_KEY")

# Настройки: 2 проверки
CHECK_ATTEMPTS = 2
CHECK_INTERVAL_FIRST = 7
CHECK_INTERVAL_SECOND = 8