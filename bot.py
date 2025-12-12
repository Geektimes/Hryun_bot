# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from database import init_db
from middlewares.db import DBSessionMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.notificator import NotificatorMiddleware
import logging
from logging.handlers import RotatingFileHandler
import os

from handlers.basic_handlers import rate_limited_router, router
from config import load_config
from utils.redis_utils import load_users_to_redis
from database import get_db

config = load_config()

bot = Bot(config.TOKEN)
dp = Dispatcher(unfiltered=True)

# Настройка логирования
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "bot.log")
log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

log_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,
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


async def main():
    logger.info("Запуск бота...")
    await init_db()

    # Загружаем пользователей в Redis
    async with get_db() as db:
        await load_users_to_redis(db)

    # Регистрируем middlewares
    dp.update.middleware(DBSessionMiddleware())
    rate_limited_router.message.middleware(RateLimitMiddleware(limit=1, period=5))
    rate_limited_router.message.middleware(NotificatorMiddleware())

    router.message.middleware(NotificatorMiddleware())

    # Регистрируем роутеры
    dp.include_router(rate_limited_router)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот успешно запущен, начинаем polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

