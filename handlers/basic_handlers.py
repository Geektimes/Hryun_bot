# handlers\basic_handlers.py
import re
import logging
from aiogram import Router
from aiogram import types
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import InputFile
from aiogram.enums import ContentType
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.orm import Session
from colorama import init, Fore
from functools import wraps

from utils.services import save_message, get_anekdot
from utils.history_listing import get_history_listing
from config import load_config
from utils.AI_model import AI_model
from database import User, Chat, Message, get_db
from utils.message_thread import get_message_thread
from utils.lock import ChatLocks

config = load_config()

# rate_limit = RateLimitMiddleware(limit=1, period=10)

ai_model = AI_model()

rate_limited_router = Router()
router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    logging.info(f"Команда /start от пользователя {message.from_user.id} в чате {message.chat.id}")

    # Сохраняем сообщение, при этом явно указываем, что бот был адресован
    await save_message(message, bot_addressed=True)

    await message.answer(config.GREETING)


@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer("Доступные команды:\n/start — начать\n/help — помощь \nНаписать разработчику - @WEB3_0_master")


@rate_limited_router.message(Command("anekdot"))
async def send_anekdot_handler(message: Message):
    # Сохраняем сообщение пользователя в базу
    await save_message(message, bot_addressed=True)
    anekdot = await get_anekdot()
    if anekdot:  # Если ответ получен
        bot_message = await message.answer(anekdot)
        await save_message(bot_message, bot_addressed=True)


@router.message(lambda msg: msg.text and msg.text.strip().lower() == "хрюн анекдот")
async def anekdot_handler(message: Message):
    # Сохраняем сообщение пользователя в базу
    await save_message(message, bot_addressed=True)
    anekdot = await get_anekdot()
    if anekdot:  # Если ответ получен
        bot_message = await message.answer(anekdot)
        await save_message(bot_message, bot_addressed=True)



@router.message(Command("broadcast"), F.chat.type == "private")
async def broadcast_message(message: Message):
    """Рассылает сообщение во все чаты, где состоит бот"""
    # Проверяем, что отправитель - владелец бота
    if str(message.from_user.id) not in [config.OWNER_BRO_ID, config.OWNER_TIM_ID]:
        await message.answer("У вас нет прав на использование этой команды.")
        return

    async with get_db() as db:
        # Получаем все чаты из базы данных
        result = await db.execute(select(Chat))
        chats = result.scalars().all()

        if not chats:
            await message.answer("Бот не состоит ни в одном чате.")
            return

        success = 0
        failed = 0
        errors = []

        # Определяем тип контента и формируем параметры для отправки
        content_type = message.content_type
        send_args = {"chat_id": None}  # Будет заполняться для каждого чата

        if content_type == ContentType.TEXT:
            # Для текстовых сообщений убираем команду /broadcast
            if message.text.startswith('/broadcast'):
                text = ' '.join(message.text.split()[1:])
                if not text:
                    await message.answer("Добавьте текст или медиа для рассылки")
                    return
                send_args["text"] = text
            else:
                send_args["text"] = message.text
        elif content_type == ContentType.PHOTO:
            send_args["photo"] = message.photo[-1].file_id
            if message.caption:
                send_args["caption"] = message.caption
        elif content_type == ContentType.VIDEO:
            send_args["video"] = message.video.file_id
            if message.caption:
                send_args["caption"] = message.caption
        elif content_type == ContentType.DOCUMENT:
            send_args["document"] = message.document.file_id
            if message.caption:
                send_args["caption"] = message.caption
        elif content_type == ContentType.AUDIO:
            send_args["audio"] = message.audio.file_id
            if message.caption:
                send_args["caption"] = message.caption
        elif content_type == ContentType.VOICE:
            send_args["voice"] = message.voice.file_id
        elif content_type == ContentType.ANIMATION:
            send_args["animation"] = message.animation.file_id
            if message.caption:
                send_args["caption"] = message.caption
        else:
            await message.answer("Этот тип сообщения не поддерживается для рассылки")
            return

        # Отправляем сообщение в каждый чат
        for chat in chats:
            try:
                send_args["chat_id"] = chat.tg_chat_id

                if content_type == ContentType.TEXT:
                    await message.bot.send_message(**send_args)
                elif content_type == ContentType.PHOTO:
                    await message.bot.send_photo(**send_args)
                elif content_type == ContentType.VIDEO:
                    await message.bot.send_video(**send_args)
                elif content_type == ContentType.DOCUMENT:
                    await message.bot.send_document(**send_args)
                elif content_type == ContentType.AUDIO:
                    await message.bot.send_audio(**send_args)
                elif content_type == ContentType.VOICE:
                    await message.bot.send_voice(**send_args)
                elif content_type == ContentType.ANIMATION:
                    await message.bot.send_animation(**send_args)

                success += 1
            except Exception as e:
                logging.error(f"Ошибка при отправке в чат {chat.tg_chat_id}: {e}")
                failed += 1
                errors.append(f"Чат {chat.tg_chat_id}: {str(e)}")
                if len(errors) > 5:
                    break

        report = (
            f"Рассылка завершена:\n"
            f"Тип контента: {content_type}\n"
            f"Успешно: {success}\n"
            f"Не удалось: {failed}"
        )

        if errors:
            report += "\n\nПоследние ошибки:\n" + "\n".join(errors[:5])

        await message.answer(report)


# ответ в личке
@router.message(F.chat.type == "private", F.text)
async def private_chat_handler(message: Message):
    logging.info(f"Сообщение в личке {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")
    await save_message(message, bot_addressed=True)
    role = 'assistant' if message.text.lower().startswith('хрюш') else 'hryn'
    bot_text = ai_model.ask(message.text, role=role)
    if bot_text:
        bot_message = await message.answer(bot_text)
        await save_message(bot_message, bot_addressed=True)


@router.message(lambda msg: msg.text and msg.text.lower().startswith("отчет"))
async def report_handler(message: Message):
    chat_lock = ChatLocks.get_lock(message.chat.id)

    if chat_lock.locked():
        # await message.answer("Подождите, предыдущий отчет еще формируется...")
        return

    async with chat_lock:
        try:
            match = re.match(r'^отчет\s+([1-9][0-9]{0,2})$', message.text.lower())
            if match:
                limit = min(int(match.group(1)), 200)
            else:
                limit = 100

            history_listing = await get_history_listing(message.chat.id, limit=limit)

            logging.info(f"Отчет для чата {message.chat.id}:\n{history_listing}")
            bot_text = ai_model.ask(history_listing, role='summary')

            if bot_text:
                await message.answer(bot_text, reply_to_message_id=message.message_id)
        except Exception as e:
            logging.error(f"Ошибка при формировании отчета: {e}")
            await message.answer("отчета не будет")


# Обработка "хрюша ..."
@router.message(lambda msg: msg.text and msg.text.lower().startswith("хрюша"))
async def assistant_handler(message: Message):
    logging.info(f"Сообщение в группе для 'хрюша' {message.chat.id} от {message.from_user.id}: {Fore.WHITE}{message.text}")
    await save_message(message, bot_addressed=True)
    bot_text = ai_model.ask(message.text, role="assistant")
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

    bot_text = ai_model.ask(message.text, role='hryn', context=context)
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

