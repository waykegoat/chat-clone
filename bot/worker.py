import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot_with_retry():
    """Запуск бота с повторными попытками"""
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            logger.info(f"🔄 Попытка запуска бота #{retry_count + 1}")
            
            # Импортируем и запускаем бота
            from bot.main import SimpleBot
            bot = SimpleBot()
            bot.init_database()
            bot.run()
            
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Ошибка: {e}")
            
            if retry_count < max_retries:
                wait_time = min(30, 5 * retry_count)  # Экспоненциальная задержка
                logger.info(f"⏳ Повтор через {wait_time} секунд...")
                time.sleep(wait_time)
            else:
                logger.error(f"🚫 Достигнут максимум попыток ({max_retries})")
                raise

if __name__ == "__main__":
    run_bot_with_retry()