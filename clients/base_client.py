from abc import ABC, abstractmethod
from typing import Optional, List, Dict

class BaseEmailClient(ABC):
    """Базовый класс для всех email клиентов"""
    
    @abstractmethod
    def get_inbox(self, email: str, password: str = None) -> List[Dict]:
        """Получение списка входящих писем"""
        pass
    
    @abstractmethod
    def get_message_content(self, message_id: str, email: str = None, password: str = None) -> Optional[Dict]:
        """Получение содержимого письма по ID"""
        pass
    
    @abstractmethod
    def find_facebook_invite(self, email: str, password: str = None, attempts: int = 2, interval_first: int = 7, interval_second: int = 8) -> Optional[str]:
        """Поиск приглашения от Facebook"""
        pass