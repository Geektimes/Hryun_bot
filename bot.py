# bot.py
import re
import asyncio
import logging
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
from dotenv import load_dotenv
import os
from colorama import init, Fore, Style

from LLM import LLM
from history_listing import get_history_listing
from save_message import save_message
import yaml

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

GREETING = config["GREETING"]

# Инициализация colorama
init(autoreset=True)  # autoreset=True автоматически сбрасывает цвет после каждого вывода
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('BOT2_TOKEN')
BOT_USERNAME = os.getenv('BOT2_USERNAME')

# session = AiohttpSession(proxy='http://proxy.server:3128')  # для деплоя на https://www.pythonanywhere.com/
# bot = Bot(TOKEN, session=session)  # для деплоя на https://www.pythonanywhere.com/
bot = Bot(TOKEN)
dp = Dispatcher(unfiltered=True)

if bot:
    llm = LLM()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(GREETING, parse_mode='HTML')


# Обработчик сообщений
@dp.message()
async def filter_messages(message: Message):
    tg_chat_id = message.chat.id
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username or "Без имени"
    chat_title = message.chat.title if message.chat.title else "Личный чат"
    tg_message_id = message.message_id

    reply_to_tg_message_id = None

    if message.reply_to_message:
        reply_to_tg_message_id = message.reply_to_message.message_id
        logging.info(
            f"\nСообщение REPLAY {reply_to_tg_message_id} от {message.from_user.id}: {Fore.WHITE}{message.text}")

    if message.text:
        # Сохраняем сообщение в базу
        await save_message(tg_chat_id, chat_title, tg_user_id, tg_username, text=message.text, tg_message_id=tg_message_id, reply_to_tg_message_id=reply_to_tg_message_id)
        logging.info(
            f"Сообщение в чате {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")

        # logging.info(f"BOT_USERNAME: {BOT_USERNAME}")
        # logging.info(f"Упоминание бота: {BOT_USERNAME in message.text}")
        # logging.info(
        #     f"Ответ на сообщение бота: {message.reply_to_message and message.reply_to_message.from_user.id == bot.id}")
        # logging.info(f"Начинается с 'хрю': {message.text.strip().lower().startswith('хрю')}")
        # logging.info(f"Начинается с 'хрюш': {message.text.strip().lower().startswith('хрюш')}")

        if message.text.strip().lower().startswith('отчет'):
            match = re.match(r'^отчет\s+(\d+)$', message.text.strip().lower())
            limit = 100  # Значение по умолчанию
            if match:
                limit = int(match.group(1))  # Извлекаем число из команды

            # def get_summary(tg_chat_id: int, limit: int = 100)
            history_listing = get_history_listing(tg_chat_id, limit=limit)

            logging.info(f"Отчет для чата {tg_chat_id}:\n{history_listing}")
            bot_text = llm.ask(history_listing, role='summary')
            await message.answer(bot_text)

        elif message.text.strip().lower().startswith('хрюш'):
            bot_text = llm.ask(message.text, role='assistant')
            await message.answer(bot_text)

        elif (BOT_USERNAME in message.text or
                (message.reply_to_message and
                 message.reply_to_message.from_user.id == bot.id) or
                message.text.strip().lower().startswith('хрю')):
            bot_text = llm.ask(message.text, role='hryn')
            await message.answer(bot_text)
        else:
            return None

        # Сохраняем ответ бота в БД
        await save_message(tg_chat_id, chat_title, 0, "Хрюн Моржов", bot_text, tg_message_id=tg_message_id)
    else:
        logging.info(f"Сообщение в чате {message.chat.id} от {message.from_user.id}: [Нет текста]")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())