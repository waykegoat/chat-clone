import time
import logging
from bot.main import ChatCloneBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """Запуск бота с перезапуском при ошибках"""
    while True:
        try:
            logger.info("🤖 Запуск Chat Clone Bot...")
            bot = ChatCloneBot()
            bot.run()
        except Exception as e:
            logger.error(f"❌ Ошибка в боте: {e}")
            logger.info("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()