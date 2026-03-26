import requests
import time
import re
from typing import Optional, List, Dict

class GmailnatorClient:
    def __init__(self):
        from config import RAPIDAPI_KEY, RAPIDAPI_HOST
        self.base_url = "https://gmailnator.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
    
    def get_inbox(self, email: str) -> List[Dict]:
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
            print(f"Ошибка получения списка писем: {e}")
            return []
    
    def get_message_content(self, message_id: str) -> Optional[Dict]:
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
    
    def find_facebook_invite(self, email: str, timeout: int = 300, check_interval: int = 10) -> Optional[str]:
        """Поиск приглашения от Facebook в почтовом ящике"""
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            print(f"[{attempt}] Проверяю почту {email}...")
            messages = self.get_inbox(email)
            
            for message in messages:
                sender = message.get('from', '').lower()
                subject = message.get('subject', '')
                
                if 'facebookmail.com' in sender:
                    message_id = message.get('id')
                    if not message_id:
                        continue
                    
                    print(f"📧 Найдено письмо от Facebook!")
                    print(f"   От: {sender}")
                    print(f"   Тема: {subject}")
                    
                    message_data = self.get_message_content(message_id)
                    if message_data:
                        content = message_data.get('content', '')
                        invite_link = self._extract_invite_link(content)
                        if invite_link:
                            print(f"✅ Ссылка найдена: {invite_link[:80]}...")
                            return invite_link
                        else:
                            print("⚠️ Ссылка не найдена в содержимом")
            
            print(f"⏳ Писем от Facebook нет. Следующая проверка через {check_interval} сек...")
            time.sleep(check_interval)
        
        print(f"❌ Время ожидания истекло ({timeout} сек)")
        return None
    
    def _extract_invite_link(self, content: str) -> Optional[str]:
        """Извлечение ссылки-приглашения из HTML-содержимого письма"""
        if not content:
            return None
        
        # Паттерны для поиска ссылок
        patterns = [
            r'https://business\.facebook\.com/invitation/\?token=[A-Za-z0-9_-]+',
            r'https://business\.facebook\.com/security/invite/\?token=[A-Za-z0-9_-]+',
            r'https://(?:www\.)?facebook\.com/business/invitation/\?token=[A-Za-z0-9_-]+',
            r'https://fb\.me/[A-Za-z0-9]+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Ищем ссылку внутри href атрибутов
        href_pattern = r'href=["\'](https://business\.facebook\.com/invitation/\?token=[A-Za-z0-9_-]+)["\']'
        matches = re.findall(href_pattern, content, re.IGNORECASE)
        if matches:
            return matches[0]
        
        return None