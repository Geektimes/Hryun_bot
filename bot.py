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

from LLM import Qwen, LLM
from save_message import save_message


# Инициализация colorama
init(autoreset=True)  # autoreset=True автоматически сбрасывает цвет после каждого вывода
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('BOT2_TOKEN')
BOT_USERNAME = os.getenv('BOT2_USERNAME')
GREETING = os.getenv('GREETING')

# session = AiohttpSession(proxy='http://proxy.server:3128')  # для деплоя на https://www.pythonanywhere.com/
# bot = Bot(TOKEN, session=session)  # для деплоя на https://www.pythonanywhere.com/
bot = Bot(TOKEN)
dp = Dispatcher()

if bot:
    llm = LLM()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(GREETING, parse_mode='HTML')

# Обработчик сообщений
@dp.message()
async def filter_messages(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or "Без имени"
    text = message.text

    # Сохраняем сообщение в базу
    await save_message(chat_id, user_id, username, text)


    if message.text:
        logging.info(
            f"Сообщение в чате {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")

        # logging.info(f"BOT_USERNAME: {BOT_USERNAME}")
        # logging.info(f"Упоминание бота: {BOT_USERNAME in message.text}")
        # logging.info(
        #     f"Ответ на сообщение бота: {message.reply_to_message and message.reply_to_message.from_user.id == bot.id}")
        # logging.info(f"Начинается с 'хрю': {message.text.strip().lower().startswith('хрю')}")
        # logging.info(f"Начинается с 'хрюш': {message.text.strip().lower().startswith('хрюш')}")

        if message.text.strip().lower().startswith('отчет'):
            chat_id = message.chat.id
            messages = bot.history(chat_id, limit=100)
            last_messages = await get_last_messages(chat_id)

            logging.info(f"\n\n\n\nПоследние {Fore.WHITE}{len(last_messages)} сообщений из чата {Fore.WHITE}{chat_id}:")
            for msg in last_messages:
                logging.info(f"{msg.date} - {msg.from_user.username or msg.from_user.id}: {Fore.WHITE}{msg.text}")
            return None

        elif message.text.strip().lower().startswith('хрюш'):
            role = 'assistant'

        elif (BOT_USERNAME in message.text or
                (message.reply_to_message and
                 message.reply_to_message.from_user.id == bot.id) or
                message.text.strip().lower().startswith('хрю')):
            role = 'hryn'
        else:
            return

        bot_text = llm.ask(message.text, role=role)
        await message.answer(bot_text)
    else:
        logging.info(f"Сообщение в чате {message.chat.id} от {message.from_user.id}: [Нет текста]")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())