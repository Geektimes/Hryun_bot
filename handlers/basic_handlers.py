# handlers\basic_handlers.py
import re
import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.orm import Session

from colorama import init, Fore

from utils.services import save_message, get_anekdot
from utils.history_listing import get_history_listing
from config import load_config
from utils.AI import LLM
from database import User, Chat, Message, get_db
from utils.message_thread import get_message_thread

config = load_config()

llm = LLM()

router = Router()

# Инициализация colorama
init(autoreset=True)  # autoreset=True автоматически сбрасывает цвет после каждого вывода
logging.basicConfig(level=logging.INFO)

@router.message(CommandStart())
async def start_handler(message: types.Message, db: Session):
    # Сохраняем пользователя
    user = db.query(User).filter_by(tg_user_id=message.from_user.id).first()
    if not user:
        user = User(
            tg_user_id=message.from_user.id,
            tg_username=message.from_user.username,
            tg_first_name=message.from_user.first_name,
            tg_last_name=message.from_user.last_name,
            is_bot=message.from_user.is_bot
        )
        db.add(user)
        db.commit()

    await message.answer(config.GREETING, parse_mode='HTML')


@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer("Доступные команды:\n/start — начать\n/help — помощь")


@router.message(lambda msg: msg.text and msg.text.strip().lower() == "хрюн анекдот")
async def anekdot_handler(message: Message):
    # Сохраняем сообщение пользователя в базу
    await save_message(message, bot_addressed=True)
    anekdot = await get_anekdot()
    if anekdot:  # Если ответ получен
        bot_message = await message.answer(anekdot)
        await save_message(bot_message, bot_addressed=True)


# 1. Ответ в личке
@router.message(F.chat.type == "private", F.text)
async def private_chat_handler(message: Message):
    logging.info(f"Сообщение в личке {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")
    await save_message(message, bot_addressed=True)
    role = 'assistant' if message.text.lower().startswith('хрюш') else 'hryn'
    bot_text = llm.ask(message.text, role=role)
    if bot_text:
        bot_message = await message.answer(bot_text)
        await save_message(bot_message, bot_addressed=True)


# Обработка "отчет N"
@router.message(lambda msg: msg.text and msg.text.lower().startswith("отчет"))
async def report_handler(message: Message):
    match = re.match(r'^отчет\s+(\d+)$', message.text.lower())
    limit = int(match.group(1)) if match else 100
    history_listing = await get_history_listing(message.chat.id, limit=limit)

    logging.info(f"Отчет для чата {message.chat.id}:\n{history_listing}")
    bot_text = llm.ask(history_listing, role='summary')
    if bot_text:
        await message.answer(bot_text)


# Обработка "хрюша ..."
@router.message(lambda msg: msg.text and msg.text.lower().startswith("хрюша"))
async def assistant_handler(message: Message):
    logging.info(f"Сообщение в группе для 'хрюша' {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")
    await save_message(message, bot_addressed=True)
    bot_text = llm.ask(message.text, role="assistant")
    if bot_text:
        bot_message = await message.answer(bot_text, reply_to_message_id=message.message_id)
        await save_message(bot_message, bot_addressed=True)


# Обработка упоминания бота или "хрюн ..."
@router.message(lambda msg: msg.text and (
    (msg.reply_to_message and msg.reply_to_message.from_user.is_bot)  # Ответ на сообщение бота
    or msg.text.lower().startswith("хрюн")
))
async def mention_handler(message: Message):
    logging.info(
        f"Сообщение в группе для 'хрюн' {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")


    async with get_db() as db:
        context = await get_message_thread(db=db, tg_user_id=message.from_user.id, tg_chat_id=message.chat.id)

    await save_message(message, bot_addressed=True)

    bot_text = llm.ask(message.text, role='hryn', context=context)
    if bot_text:
        bot_message = await message.answer(bot_text, reply_to_message_id=message.message_id)
        await save_message(bot_message, bot_addressed=True)


@router.message()
async def unknown_message_handler(message: Message):
    msg_type = "I dont know"

    if message.text:
        msg_type = "text"
    elif message.sticker:
        msg_type = "sticker"
    elif message.photo:
        msg_type = "photo"
    elif message.video:
        msg_type = "video"
    elif message.voice:
        msg_type = "voice"
    elif message.audio:
        msg_type = "audio"
    elif message.document:
        msg_type = "document"
    elif message.contact:
        msg_type = "contact"
    elif message.location:
        msg_type = "location"
    elif message.animation:
        msg_type = "animation"
    elif message.video_note:
        msg_type = "video_note"
    elif message.dice:
        msg_type = "dice"
    elif message.poll:
        msg_type = "poll"
    else:
        msg_type = "unknown"

    logging.info(f"Получено сообщение типа: {msg_type}")
    await save_message(message, type=msg_type)


