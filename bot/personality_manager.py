from datetime import datetime, timedelta
from typing import Dict, Any
import json
from sqlalchemy.orm import Session

from bot.database import Chat, Statistic

class PersonalityManager:
    def __init__(self):
        self.personality_templates = {
            1: {"name": "Робот", "description": "Просто комбинирует слова"},
            2: {"name": "Новичок", "description": "Использует простые шаблоны"},
            3: {"name": "Свой", "description": "Имитирует стиль чата"},
            4: {"name": "Гуру", "description": "Мастер подколов и отсылок"}
        }
    
    def check_level_up(self, chat_id: int, db: Session) -> bool:
        """Проверка возможности повышения уровня"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return False
        
        # Получаем статистику за последние 7 дней
        week_ago = datetime.now() - timedelta(days=7)
        stats = db.query(Statistic).filter(
            Statistic.chat_id == chat_id,
            Statistic.date >= week_ago
        ).all()
        
        if not stats:
            return False
        
        # Расчет эффективности
        total_messages = sum(s.total_messages for s in stats)
        bot_responses = sum(s.bot_responses for s in stats)
        
        if total_messages == 0:
            return False
        
        response_rate = bot_responses / total_messages
        engagement_rate = self._calculate_engagement(chat_id, db)
        
        # Логика повышения уровня
        if chat.personality_level == 1 and total_messages > 100:
            return True
        elif chat.personality_level == 2 and response_rate > 0.25 and engagement_rate > 0.3:
            return True
        elif chat.personality_level == 3 and response_rate > 0.4 and engagement_rate > 0.5:
            return True
        
        return False
    
    def _calculate_engagement(self, chat_id: int, db: Session) -> float:
        """Расчет вовлеченности"""
        # Здесь можно добавить логику анализа реакций на сообщения бота
        return 0.3  # Заглушка
    
    def reset_personality(self, chat_id: int, db: Session):
        """Сброс личности"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            chat.personality_level = 1
            chat.learning_mode = True
            chat.learning_end_time = datetime.now() + timedelta(hours=72)
            db.commit()