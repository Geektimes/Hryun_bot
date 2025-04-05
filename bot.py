# bot.py
import re
import asyncio
import logging
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
from dotenv import load_dotenv
import os
from colorama import init, Fore, Style
import yaml

from LLM import LLM, requests_limit
from history_listing import get_history_listing
from services import save_message, get_anekdot
from database import init_db

init_db()

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

GREETING = config["GREETING"]

# Инициализация colorama
init(autoreset=True)  # autoreset=True автоматически сбрасывает цвет после каждого вывода
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')

# session = AiohttpSession(proxy='http://proxy.server:3128')  # для деплоя на https://www.pythonanywhere.com/
# bot = Bot(TOKEN, session=session)  # для деплоя на https://www.pythonanywhere.com/
bot = Bot(TOKEN)
dp = Dispatcher(unfiltered=True)

if bot:
    llm = LLM()

def reduction_requests_limit():
    global requests_limit
    requests_limit -= 1


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(GREETING, parse_mode='HTML')


@dp.message(F.text.regexp(r"(?i)^хрюн анекдот$"))
async def anekdot_handler(message: Message):
    tg_chat_id = message.chat.id
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username or ""
    tg_first_name = message.from_user.first_name  # Имя пользователя
    tg_last_name = message.from_user.last_name or ""  # Фамилия (может быть пустой)
    chat_title = message.chat.title if message.chat.title else f"Личный чат с {tg_first_name}"
    tg_message_id = message.message_id
    reply_to_tg_message_id = None

    if message.reply_to_message:
        reply_to_tg_message_id = message.reply_to_message.message_id

    # Сохраняем сообщение пользователя в базу
    await save_message(
        tg_chat_id=tg_chat_id,
        chat_title=chat_title,
        tg_user_id=tg_user_id,
        tg_username=tg_username,
        tg_first_name=tg_first_name,
        tg_last_name=tg_last_name,
        content=message.text,
        tg_message_id=tg_message_id,
        bot_addressed=True,
        reply_to_tg_message_id=reply_to_tg_message_id
    )
    anekdot = await get_anekdot()
    if anekdot:  # Если ответ получен
        bot_message = await message.answer(anekdot)

        # Сохраняем ответ бота
        await save_message(
            tg_chat_id=tg_chat_id,
            chat_title=chat_title,
            tg_user_id=7858823954,
            tg_username="@hryun2_bot",
            tg_first_name="Хрюн",
            tg_last_name="Моржов",
            content="*рассказывает анекдот",
            tg_message_id=bot_message.message_id,  # Используем ID отправленного сообщения
            bot_addressed=True,
            reply_to_tg_message_id=tg_message_id
        )


# Обработчик сообщений
@dp.message()
async def filter_messages(message: Message):
    tg_chat_id = message.chat.id
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username or ""
    tg_first_name = message.from_user.first_name  # Имя пользователя
    tg_last_name = message.from_user.last_name or ""  # Фамилия (может быть пустой)
    chat_title = message.chat.title if message.chat.title else f"Личный чат с {tg_first_name}"
    tg_message_id = message.message_id
    reply_to_tg_message_id = None

    if message.reply_to_message:
        reply_to_tg_message_id = message.reply_to_message.message_id

    if message.text:
        logging.info(
            f"Сообщение в чате {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")

        # Сохраняем сообщение пользователя в базу
        await save_message(
            tg_chat_id=tg_chat_id,
            chat_title=chat_title,
            tg_user_id=tg_user_id,
            tg_username=tg_username,
            tg_first_name=tg_first_name,
            tg_last_name=tg_last_name,
            content=message.text,
            tg_message_id=tg_message_id,
            bot_addressed=True,
            reply_to_tg_message_id=reply_to_tg_message_id
        )

        # Если это личный чат, отвечаем сразу без условий
        if message.chat.type == "private":
            if message.text.strip().lower().startswith('хрюш'):
                current_role = 'assistant'
            else:
                current_role = 'hryn'

            bot_text = llm.ask(message.text, role=current_role)
            if bot_text:  # Если ответ получен
                reduction_requests_limit()
                bot_message = await message.answer(bot_text)

                # Сохраняем ответ бота
                await save_message(
                    tg_chat_id=tg_chat_id,
                    chat_title=chat_title,
                    tg_user_id=7858823954,
                    tg_username="@hryun2_bot",
                    tg_first_name="Хрюн",
                    tg_last_name="Моржов",
                    content=bot_text,
                    tg_message_id=bot_message.message_id,  # Используем ID отправленного сообщения
                    bot_addressed=True,
                    reply_to_tg_message_id=tg_message_id
                )

            return

        elif message.text.strip().lower().startswith('отчет'):
            match = re.match(r'^отчет\s+(\d+)$', message.text.strip().lower())
            limit = 100  # Значение по умолчанию
            if match:
                limit = int(match.group(1))  # Извлекаем число из команды

            # def get_summary(tg_chat_id: int, limit: int = 100)
            history_listing = get_history_listing(tg_chat_id, limit=limit)

            logging.info(f"Отчет для чата {tg_chat_id}:\n{history_listing}")
            bot_text = llm.ask(history_listing, role='summary')
            if bot_text:  # Если ответ получен
                reduction_requests_limit()
                await message.answer(bot_text)
            return

        elif message.text.strip().lower().startswith('хрюша'):
            bot_text = llm.ask(message.text, role='assistant')
            if bot_text:  # Если ответ получен
                reduction_requests_limit()
                await message.answer(bot_text, reply_to_message_id=message.message_id)

        elif (BOT_USERNAME in message.text or
                (message.reply_to_message and
                 message.reply_to_message.from_user.id == bot.id) or
                message.text.strip().lower().startswith('хрюн')):

            # Сохраняем сообщение пользователя перед тем, как бот ответит
            await save_message(
                tg_chat_id=tg_chat_id,
                chat_title=chat_title,
                tg_user_id=tg_user_id,
                tg_username=tg_username,
                tg_first_name=tg_first_name,
                tg_last_name=tg_last_name,
                content=message.text,
                tg_message_id=tg_message_id,
                bot_addressed=True,
                reply_to_tg_message_id=reply_to_tg_message_id
            )

            bot_text = llm.ask(message.text, role='hryn')
            if bot_text:  # Если ответ получен
                reduction_requests_limit()

                # Отправляем сообщение и получаем объект Message
                sent_message = await message.answer(bot_text, reply_to_message_id=message.message_id)

                # Сохраняем ответ бота
                await save_message(
                    tg_chat_id=tg_chat_id,
                    chat_title=chat_title,
                    tg_user_id=7858823954,
                    tg_username="@hryun2_bot",
                    tg_first_name="Хрюн",
                    tg_last_name="Моржов",
                    content=bot_text,
                    tg_message_id=sent_message.message_id,  # Используем ID отправленного сообщения
                    bot_addressed=True,
                    reply_to_tg_message_id=tg_message_id
                )
        else:
            return None

    else:
        logging.info(f"Сообщение в чате {message.chat.id} от {message.from_user.id}: [Нет текста]")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())