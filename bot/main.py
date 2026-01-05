import os
import sys
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверка установленных зависимостей"""
    try:
        import telebot
        logger.info("✅ pyTelegramBotAPI установлен")
    except ImportError:
        logger.error("❌ pyTelegramBotAPI не установлен")
        return False
    
    try:
        import sqlalchemy
        logger.info("✅ SQLAlchemy установлен")
    except ImportError:
        logger.error("❌ SQLAlchemy не установлен")
        return False
    
    try:
        import flask
        logger.info("✅ Flask установлен")
    except ImportError:
        logger.warning("⚠️ Flask не установлен (требуется только для веб-панели)")
    
    return True

class SimpleBot:
    def __init__(self):
        # Проверяем зависимости
        if not check_dependencies():
            logger.error("❌ Не все зависимости установлены")
            sys.exit(1)
        
        # Импортируем после проверки
        import telebot
        from sqlalchemy import create_engine, text
        
        # Получаем токен
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            logger.error("❌ TELEGRAM_TOKEN не найден!")
            logger.info("💡 Добавьте TELEGRAM_TOKEN в переменные окружения Railway")
            sys.exit(1)
        
        self.bot = telebot.TeleBot(self.token)
        self.db_url = os.getenv('DATABASE_URL')
        
        if self.db_url and self.db_url.startswith("postgres://"):
            self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
        
        logger.info(f"✅ Бот инициализирован. Токен: {self.token[:15]}...")
        self.setup_handlers()
    
    def init_database(self):
        """Инициализация базы данных (упрощенная)"""
        if not self.db_url:
            logger.warning("⚠️ DATABASE_URL не установлен, работаю без БД")
            return None
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.db_url)
            
            # Создаем таблицу если не существует
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT,
                        user_id BIGINT,
                        username VARCHAR(255),
                        message_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
            
            logger.info("✅ База данных инициализирована")
            return engine
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            return None
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        import telebot
        import random
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = """
🤖 *Chat Clone Bot v1.0*

*Доступные команды:*
/start - Приветствие
/help - Помощь
/stats - Статистика
/reset - Сбросить обучение

*Режимы работы:*
1. Обучение (72 часа) - собираю фразы из чата
2. Активный режим - отвечаю на сообщения

Отправьте любое сообщение, чтобы начать!
            """
            self.bot.reply_to(message, welcome_text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['stats'])
        def send_stats(message):
            try:
                from sqlalchemy import create_engine, text
                if self.db_url:
                    engine = create_engine(self.db_url)
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT COUNT(*) FROM messages"))
                        count = result.scalar() or 0
                    
                    stats_text = f"""
📊 *Статистика бота:*

*Сообщений в базе:* {count}
*Режим:* Обучение
*Версия:* 1.0
                    """
                else:
                    stats_text = "📊 База данных не настроена"
                
                self.bot.reply_to(message, stats_text, parse_mode='Markdown')
            except Exception as e:
                self.bot.reply_to(message, f"❌ Ошибка: {str(e)}")
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            # Сохраняем сообщение в БД
            try:
                if self.db_url:
                    from sqlalchemy import create_engine, text
                    engine = create_engine(self.db_url)
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO messages (chat_id, user_id, username, message_text)
                            VALUES (:chat_id, :user_id, :username, :message_text)
                        """), {
                            'chat_id': message.chat.id,
                            'user_id': message.from_user.id,
                            'username': message.from_user.username or message.from_user.first_name,
                            'message_text': message.text
                        })
                        conn.commit()
            except Exception as e:
                logger.error(f"Ошибка сохранения в БД: {e}")
            
            # Простые ответы
            responses = [
                "Интересное сообщение! 🤔",
                "Запомнил эту фразу! 📝",
                "Продолжайте общаться, я учусь! 🎓",
                "Спасибо за сообщение! 🙏",
                "Отличная мысль! 💭",
                "А что вы об этом думаете? 💬",
                "Продолжайте в том же духе! 🚀",
                "Записал в базу знаний! 🗂️",
                "Интересный паттерн речи! 🎯",
                "Учусь на ваших разговорах... 🧠"
            ]
            
            # Отвечаем с вероятностью 30%
            if random.random() < 0.3:
                response = random.choice(responses)
                self.bot.reply_to(message, response)
            
            logger.info(f"📨 Сообщение от @{message.from_user.username}: {message.text[:50]}...")
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Запускаю Telegram бота...")
        try:
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Ошибка в боте: {e}")
            raise

def main():
    """Основная функция запуска"""
    logger.info("=" * 50)
    logger.info("🤖 ЗАПУСК CHAT CLONE BOT")
    logger.info("=" * 50)
    
    # Задержка для гарантированной установки зависимостей
    time.sleep(5)
    
    # Создаем и запускаем бота
    bot = SimpleBot()
    bot.init_database()  # Инициализируем БД
    bot.run()

if __name__ == "__main__":
    main()