import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from bot.database import Pattern, Message, Chat, User
from bot.personality_manager import PersonalityManager
from bot.config import Config

class ResponseGenerator:
    def __init__(self, personality_manager: PersonalityManager):
        self.personality = personality_manager
        self.last_response_time = {}
        
    def should_respond(self, chat_id: str) -> bool:
        """Определить, должен ли бот ответить"""
        current_time = datetime.now()
        
        # Rate limiting
        if chat_id in self.last_response_time:
            time_diff = (current_time - self.last_response_time[chat_id]).total_seconds()
            if time_diff < Config.RATE_LIMIT_SECONDS:
                return False
        
        # Вероятность ответа
        if random.random() > Config.RESPONSE_RATE:
            return False
            
        return True
    
    def generate_response(self, chat_id: int, context: Dict, db: Session) -> Optional[str]:
        """Генерация ответа на основе контекста"""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        
        # Получение релевантных паттернов
        patterns = self._get_relevant_patterns(chat_id, context, db)
        
        if not patterns:
            return None
        
        # Генерация ответа в зависимости от уровня личности
        if chat.personality_level == 1:
            response = self._generate_robot_response(patterns)
        elif chat.personality_level == 2:
            response = self._generate_novice_response(patterns, context, db)
        elif chat.personality_level == 3:
            response = self._generate_member_response(patterns, context, db)
        else:  # level 4
            response = self._generate_guru_response(patterns, context, db)
        
        # Обновление времени ответа
        self.last_response_time[str(chat.chat_id)] = datetime.now()
        
        return response
    
    def _get_relevant_patterns(self, chat_id: int, context: Dict, db: Session) -> List[Pattern]:
        """Получение релевантных паттернов"""
        # Получаем последние сообщения для контекста
        recent_messages = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.text.isnot(None)
        ).order_by(desc(Message.timestamp)).limit(10).all()
        
        # Извлекаем ключевые слова
        keywords = set()
        for msg in recent_messages:
            if msg.text:
                words = msg.text.lower().split()
                keywords.update([w for w in words if len(w) > 3])
        
        # Ищем паттерны с этими словами
        patterns = []
        for keyword in list(keywords)[:5]:  # Берем первые 5 ключевых слов
            matched = db.query(Pattern).filter(
                Pattern.chat_id == chat_id,
                Pattern.pattern_text.like(f'%{keyword}%'),
                Pattern.pattern_type.in_(['word', 'bigram', 'trigram'])
            ).order_by(desc(Pattern.frequency)).limit(3).all()
            patterns.extend(matched)
        
        return list(set(patterns))
    
    def _generate_robot_response(self, patterns: List[Pattern]) -> str:
        """Генерация ответа уровня 1 (Робот)"""
        if not patterns:
            return random.choice(["Да", "Нет", "Интересно", "Понятно"])
        
        # Простая комбинация слов
        words = []
        for pattern in patterns[:3]:
            if pattern.pattern_text:
                words.extend(pattern.pattern_text.split())
        
        if words:
            response_words = random.sample(words, min(3, len(words)))
            return ' '.join(response_words).capitalize() + random.choice(['.', '!', '...'])
        
        return "Что?"
    
    def _generate_novice_response(self, patterns: List[Pattern], context: Dict, db: Session) -> str:
        """Генерация ответа уровня 2 (Новичок)"""
        # Используем простые шаблоны
        templates = [
            "Я тоже думаю про {word}",
            "{word} - это интересно",
            "А что насчет {word}?",
            "Помню, мы говорили про {word}"
        ]
        
        if patterns:
            word = random.choice(patterns).pattern_text.split()[0]
            template = random.choice(templates)
            return template.format(word=word)
        
        return random.choice(["Согласен", "Не уверен", "Может быть"])