import requests
import time
import re
from typing import Optional, List, Dict
from .base_client import BaseEmailClient

class GmailnatorClient(BaseEmailClient):
    def __init__(self, api_key: str, api_host: str):
        self.base_url = "https://gmailnator.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host,
            "Content-Type": "application/json"
        }
    
    def get_inbox(self, email: str, password: str = None) -> List[Dict]:
        """Получение списка входящих писем"""
        try:
            response = requests.post(
                f"{self.base_url}/api/inbox",
                json={"email": email},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                return data.get('messages', [])
            return []
        except Exception as e:
            print(f"Ошибка получения списка писем Gmailnator: {e}")
            return []
    
    def get_message_content(self, message_id: str, email: str = None, password: str = None) -> Optional[Dict]:
        """Получение полного содержимого письма по ID"""
        try:
            response = requests.get(
                f"{self.base_url}/api/inbox/{message_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения содержимого письма: {e}")
            return None
    
    def find_facebook_invite(self, email: str, password: str = None, attempts: int = 2, interval_first: int = 7, interval_second: int = 8) -> Optional[str]:
    """
    Поиск приглашения от Facebook в почтовом ящике
    Делает 2 попытки: через 7 секунд и через 15 секунд
    """
    facebook_senders = [
        'facebookmail.com',
        'business.facebook.com', 
        'noreply@business.facebook.com',
        'notification@facebookmail.com'
    ]
    
    intervals = [interval_first, interval_second]
    
    for attempt in range(1, attempts + 1):
        print(f"[Gmailnator Попытка {attempt}/{attempts}] Проверяю почту {email}...")
        messages = self.get_inbox(email)
        
        for message in messages:
            sender = message.get('from', '').lower()
            
            is_facebook = any(fb_sender in sender for fb_sender in facebook_senders)
            
            if is_facebook:
                message_id = message.get('id')
                if not message_id:
                    continue
                
                print(f"📧 Найдено письмо от Facebook! Отправитель: {sender}")
                
                message_data = self.get_message_content(message_id)
                if message_data:
                    content = message_data.get('content', '')
                    invite_link = self._extract_invite_link(content)
                    if invite_link:
                        print(f"✅ Ссылка найдена на попытке {attempt}")
                        return invite_link
                    else:
                        print("⚠️ Ссылка не найдена в содержимом")
        
        if attempt < attempts:
            wait_time = intervals[attempt - 1]
            print(f"⏳ Писем от Facebook нет. Следующая проверка через {wait_time} сек...")
            time.sleep(wait_time)
    
    print(f"❌ Письмо не обнаружено после {attempts} попыток")
    return None
    
    def _extract_invite_link(self, content: str) -> Optional[str]:
        """Извлечение ссылки-приглашения из HTML-содержимого письма"""
        if not content:
            return None
        
        patterns = [
            r'https://business\.facebook\.com/invitation/\?token=[A-Za-z0-9_-]+',
            r'https://business\.facebook\.com/security/invite/\?token=[A-Za-z0-9_-]+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        token_pattern = r'https?://[^\s"\']+/invitation/\?token=[A-Za-z0-9_-]+'
        matches = re.findall(token_pattern, content, re.IGNORECASE)
        if matches:
            return matches[0]
        
        return None