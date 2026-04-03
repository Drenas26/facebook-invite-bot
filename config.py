import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Gmailnator
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

# Firstmail - используем новый ключ из теста
FIRSTMAIL_API_KEY = os.getenv("FIRSTMAIL_API_KEY", "362w_8kKJr-nt3d_fAliR0JOyYCnCd82O_PGb5LeK0Jp_Fg14q0y42-aq6HoI-ky")

# Настройки проверки
CHECK_ATTEMPTS = 3
CHECK_INTERVAL = 7