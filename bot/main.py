import asyncio
import threading
from datetime import datetime
from typing import Dict, Any

import telebot
from sqlalchemy.orm import Session

from bot.config import Config
from bot.database import init_db, get_db, SessionLocal
from bot.message_processor import MessageProcessor
from bot.pattern_learner import PatternLearner
from bot.response_generator import ResponseGenerator
from bot.personality_manager import PersonalityManager
from bot.moderation_filter import ModerationFilter

class ChatCloneBot:
    def __init__(self):
        Config.validate()
        
        # Инициализация компонентов
        self.bot = telebot.TeleBot(Config.TELEGRAM_TOKEN)
        self.db = SessionLocal()
        
        self.message_processor = MessageProcessor()
        self.pattern_learner = PatternLearner()
        self.personality_manager = PersonalityManager()
        self.moderation_filter = ModerationFilter()
        self.response_generator = ResponseGenerator(self.personality_manager)
        
        # Инициализация базы данных
        init_db()
        
        # Регистрация обработчиков
        self._register_handlers()
        
    def _register_handlers(self):
        """Регистрация обработчиков сообщений"""
        
        @self.bot.message_handler(func=lambda message: True, content_types=['text', 'sticker', 'photo'])
        def handle_message(message):
            asyncio.run(self._process_message_async(message))
        
        @self.bot.message_handler(commands=['reset_personality'])
        def reset_personality(message):
            self._handle_reset_personality(message)
        
        @self.bot.message_handler(commands=['stats'])
        def show_stats(message):
            self._handle_stats(message)
    
    async def _process_message_async(self, message: Any):
        """Асинхронная обработка сообщения"""
        with SessionLocal() as db:
            # Обработка сообщения
            result = await self.message_processor.process_message(message, db)
            
            if result['action'] == 'ignore':
                return
            
            # Модерация
            if hasattr(message, 'text') and message.text:
                if self.moderation_filter.check_message(message.text):
                    return
            
            # Обучение на сообщении
            if result['action'] == 'process':
                msg = result['message']
                chat = result['chat']
                
                if msg.text:
                    self.pattern_learner.analyze_message(
                        msg.text, chat.id, result['user'].id, db
                    )
                
                # Проверка уровня личности
                if self.personality_manager.check_level_up(chat.id, db):
                    chat.personality_level = min(4, chat.personality_level + 1)
                    db.commit()
                
                # Генерация ответа
                if not chat.learning_mode:
                    if self.response_generator.should_respond(str(message.chat.id)):
                        context = {
                            'message': msg.text,
                            'user_id': result['user'].id,
                            'chat_id': chat.id
                        }
                        response = self.response_generator.generate_response(
                            chat.id, context, db
                        )
                        
                        if response and self.moderation_filter.check_response(response):
                            self.bot.reply_to(message, response)
    
    def _handle_reset_personality(self, message):
        """Обработка команды сброса личности"""
        with SessionLocal() as db:
            chat = db.query(Chat).filter(Chat.chat_id == str(message.chat.id)).first()
            if chat:
                self.personality_manager.reset_personality(chat.id, db)
                self.bot.reply_to(message, "✅ Личность сброшена. Начинаю переобучение (72 часа).")
    
    def _handle_stats(self, message):
        """Показать статистику"""
        with SessionLocal() as db:
            chat = db.query(Chat).filter(Chat.chat_id == str(message.chat.id)).first()
            if chat:
                stats = f"""
📊 Статистика чата:
Уровень личности: {chat.personality_level} ({self.personality_manager.personality_templates[chat.personality_level]['name']})
Режим: {'Обучение' if chat.learning_mode else 'Активный'}
Сообщений обработано: {chat.messages.count() if hasattr(chat, 'messages') else 0}
                """
                self.bot.reply_to(message, stats)
    
    def run(self):
        """Запуск бота"""
        print("🤖 Чат-клон бот запущен...")
        self.bot.infinity_polling()

if __name__ == "__main__":
    bot = ChatCloneBot()
    bot.run()