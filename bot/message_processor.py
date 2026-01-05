import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from bot.database import Message, User, Chat, get_db
from bot.utils import clean_text, contains_blacklisted_words
from bot.config import Config

class MessageProcessor:
    def __init__(self):
        self.message_cache = {}
        
    async def process_message(self, message: Any, db: Session) -> Dict:
        """Обработка входящего сообщения"""
        chat_id = str(message.chat.id)
        user_id = str(message.from_user.id)
        
        # Проверка на чёрный список
        if hasattr(message, 'text') and message.text:
            if contains_blacklisted_words(message.text, Config.BLACKLIST_WORDS):
                return {'action': 'ignore', 'reason': 'blacklisted'}
        
        # Сохранение чата
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            chat = Chat(
                chat_id=chat_id,
                title=message.chat.title if hasattr(message.chat, 'title') else "Unknown",
                learning_mode=True,
                learning_end_time=datetime.now() + timedelta(hours=Config.LEARNING_HOURS)
            )
            db.add(chat)
            db.commit()
            db.refresh(chat)
        
        # Сохранение пользователя
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                message_count=1
            )
            db.add(user)
        else:
            user.message_count += 1
            user.last_seen = datetime.now()
        
        # Сохранение сообщения
        msg = Message(
            chat_id=chat.id,
            user_id=user.id,
            message_id=message.message_id,
            text=message.text if hasattr(message, 'text') else None,
            message_type=self._get_message_type(message),
            timestamp=datetime.now()
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        
        # Проверка режима обучения
        if chat.learning_mode and chat.learning_end_time:
            if datetime.now() > chat.learning_end_time:
                chat.learning_mode = False
                chat.personality_level = 2
                db.commit()
                return {'action': 'switch_to_active', 'chat': chat}
        
        return {
            'action': 'process',
            'message': msg,
            'chat': chat,
            'user': user
        }
    
    def _get_message_type(self, message: Any) -> str:
        """Определение типа сообщения"""
        if message.content_type == 'text':
            return 'text'
        elif message.content_type == 'sticker':
            return 'sticker'
        elif message.content_type == 'photo':
            return 'photo'
        elif message.content_type == 'video':
            return 'video'
        elif message.content_type == 'voice':
            return 'voice'
        else:
            return 'other'