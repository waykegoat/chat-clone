import os
import time
import logging
import telebot
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotWorker:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.database_url = os.getenv('DATABASE_URL')
        
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        self.init_database()
        self.bot = telebot.TeleBot(self.token)
        self.setup_handlers()
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            engine = create_engine(self.database_url)
            with engine.connect() as conn:
                # Создаем простую таблицу для теста
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT,
                        user_id BIGINT,
                        text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
    
    def setup_handlers(self):
        """Настройка обработчиков бота"""
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message, "🤖 Привет! Я чат-клон бот. Обучаюсь на ваших сообщениях!")
        
        @self.bot.message_handler(func=lambda message: True)
        def echo_all(message):
            # Сохраняем сообщение в БД
            try:
                engine = create_engine(self.database_url)
                with engine.connect() as conn:
                    conn.execute(text(
                        "INSERT INTO messages (chat_id, user_id, text) VALUES (:chat_id, :user_id, :text)"
                    ), {
                        'chat_id': message.chat.id,
                        'user_id': message.from_user.id,
                        'text': message.text
                    })
                    conn.commit()
            except Exception as e:
                logger.error(f"Ошибка сохранения: {e}")
            
            # Простой ответ
            responses = [
                "Интересно!",
                "Продолжайте общаться, я учусь!",
                "Запомнил это сообщение 📝",
                "Спасибо за сообщение!",
                "Учусь на ваших разговорах..."
            ]
            self.bot.reply_to(message, f"{random.choice(responses)} (Сообщение #{random.randint(1, 1000)})")
    
    def run(self):
        """Запуск бота"""
        logger.info("🤖 Запускаю Telegram бота...")
        try:
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка бота: {e}")
            raise

if __name__ == "__main__":
    import random
    
    worker = BotWorker()
    
    # Запуск с перезапуском при ошибках
    while True:
        try:
            worker.run()
        except Exception as e:
            logger.error(f"❌ Бот упал: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)