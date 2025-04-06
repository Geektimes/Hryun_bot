#bot.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers import register_handlers

# from config import config, GREETING, BOT_USERNAME, TOKEN
from config import load_config
from database import init_db
from middlewares.db import DBSessionMiddleware


config = load_config()

# session = AiohttpSession(proxy='http://proxy.server:3128')  # для деплоя на https://www.pythonanywhere.com/
# bot = Bot(TOKEN, session=session)  # для деплоя на https://www.pythonanywhere.com/
bot = Bot(config.TOKEN)
dp = Dispatcher(unfiltered=True)


async def main():
    await init_db()
    dp.update.middleware(DBSessionMiddleware())
    register_handlers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
