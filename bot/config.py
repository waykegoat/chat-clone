import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # PostgreSQL (Railway)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Redis (для кэширования)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Настройки бота
    LEARNING_HOURS = int(os.getenv('LEARNING_HOURS', 72))
    RESPONSE_RATE = float(os.getenv('RESPONSE_RATE', 0.3))
    MAX_MESSAGES_PER_DAY = int(os.getenv('MAX_MESSAGES_PER_DAY', 500))
    RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', 120))
    
    # Настройки веб-панели
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Чёрный список слов
    BLACKLIST_WORDS = [
        'политика', 'религия', 'экстремизм', 'национализм',
        'расизм', 'ксенофобия', 'порно', 'наркотики'
    ]
    
    @classmethod
    def validate(cls):
        """Проверка конфигурации"""
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN не установлен")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL не установлен")