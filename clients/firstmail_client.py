import requests
import time
import re
from typing import Optional, List, Dict
from .base_client import BaseEmailClient

class FirstmailClient(BaseEmailClient):
    def __init__(self, api_key: str):
        self.base_url = "https://firstmail.ltd/api/v1"
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
    
    def get_inbox(self, email: str, password: str = None) -> List[Dict]:
        """
        Получение списка входящих писем через /email/messages
        Для firstmail требуется пароль
        """
        if not password:
            print("Ошибка: для firstmail требуется пароль")
            return []
        
        try:
            payload = {
                "email": email,
                "password": password,
                "limit": 50,
                "folder": "INBOX"
            }
            print(f"📤 Запрос к firstmail: {email}")
            
            response = requests.post(
                f"{self.base_url}/email/messages",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('data', {}).get('messages'):
                    return data['data']['messages']
                else:
                    print(f"❌ Нет сообщений в ответе")
                    return []
            elif response.status_code == 401:
                print("❌ Неверный логин или пароль")
                return []
            else:
                print(f"❌ Ошибка HTTP {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка получения списка писем firstmail: {e}")
            return []
    
    def get_message_content(self, message_id: str, email: str = None, password: str = None) -> Optional[Dict]:
        """Получение содержимого письма по ID (не используется для firstmail)"""
        return None
    
    def find_facebook_invite(self, email: str, password: str = None, attempts: int = 3, interval: int = 7) -> Optional[str]:
        """
        Поиск приглашения от Facebook в почтовом ящике firstmail
        """
        if not password:
            print("❌ Ошибка: для firstmail требуется пароль")
            return None
        
        # Список возможных отправителей от Facebook
        facebook_senders = [
            'facebookmail.com',
            'business.facebook.com', 
            'noreply@business.facebook.com',
            'notification@facebookmail.com'
        ]
        
        for attempt in range(1, attempts + 1):
            print(f"[Firstmail Попытка {attempt}/{attempts}] Проверяю почту {email}...")
            messages = self.get_inbox(email, password)
            
            if not messages:
                print(f"⚠️ Писем не найдено или ошибка получения")
            else:
                print(f"📬 Получено {len(messages)} писем")
                
                for message in messages:
                    sender = message.get('from', '').lower()
                    subject = message.get('subject', '')
                    print(f"   Письмо: {sender} - {subject[:50]}")
                    
                    # Проверяем, что письмо от Facebook
                    is_facebook = any(fb_sender in sender for fb_sender in facebook_senders)
                    
                    if is_facebook:
                        print(f"📧 Найдено письмо от Facebook! Отправитель: {sender}")
                        
                        # Получаем содержимое
                        body_html = message.get('body_html', '')
                        body_text = message.get('body_text', '')
                        content = body_html or body_text
                        
                        invite_link = self._extract_invite_link(content)
                        if invite_link:
                            print(f"✅ Ссылка найдена на попытке {attempt}")
                            return invite_link
                        else:
                            print("⚠️ Ссылка не найдена в содержимом")
            
            if attempt < attempts:
                print(f"⏳ Следующая проверка через {interval} сек...")
                time.sleep(interval)
        
        print(f"❌ Письмо не обнаружено после {attempts} попыток")
        return None
    
    def _extract_invite_link(self, content: str) -> Optional[str]:
        """Извлечение ссылки-приглашения из содержимого письма"""
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