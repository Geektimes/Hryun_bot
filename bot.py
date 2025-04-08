# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers import register_handlers
from config import load_config
from database import init_db
from middlewares.db import DBSessionMiddleware
from middlewares.rate_limit import RateLimitMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os

# Настройка логирования с ротацией
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "bot.log")
log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

log_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8",
    delay=False
)

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

config = load_config()
bot = Bot(config.TOKEN)
dp = Dispatcher(unfiltered=True)

async def main():
    logger.info("Запуск бота...")
    await init_db()

    # Регистрируем middlewares
    dp.update.middleware(DBSessionMiddleware())  # Для работы с базой данных
    dp.message.middleware(RateLimitMiddleware(limit=1, period=10))  # 1 запрос в минуту для сообщений

    register_handlers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот успешно запущен, начинаем polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())