# history_listing.py
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, Message, User, Chat


async def get_messages_with_users(tg_chat_id: int, limit: int):
    async with get_db() as session:  # session: AsyncSession
        stmt = (
            select(Message, User)
            .join(User, Message.user_id == User.id)
            .join(Chat, Message.chat_id == Chat.id)  # Явно указываем связь с Chat
            .where(Chat.tg_chat_id == tg_chat_id)  # Фильтр по Telegram ID чата
            .order_by(Message.timestamp.desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        return result.all()


async def get_history_listing(tg_chat_id: int, limit: int = 100):
    messages = await get_messages_with_users(tg_chat_id, limit)
    if messages:
        summary = []
        async with get_db() as session:
            for chat_message, user in messages:
                username = user.tg_username or "Неизвестный"
                # Обрабатываем разные типы сообщений
                if chat_message.type == "text" or (
                        chat_message.content and chat_message.content not in ["[photo]", "[sticker]", "[video]",
                                                                              "[voice]", "[audio]", "[document]",
                                                                              "[animation]", "[video_note]", "[dice]",
                                                                              "[poll]"]):
                    message_desc = f"сказал: \"{chat_message.content}\""
                else:
                    type_map = {
                        "photo": "отправил фото",
                        "sticker": "отправил стикер",
                        "video": "отправил видео",
                        "voice": "отправил голосовое сообщение",
                        "audio": "отправил аудио",
                        "document": "отправил документ",
                        "animation": "отправил анимацию",
                        "video_note": "отправил видео-кружок",
                        "dice": "бросил кубик",
                        "poll": "создал опрос"
                    }
                    message_desc = type_map.get(chat_message.type, f"отправил что-то странное ({chat_message.type})")

                # Проверяем, является ли сообщение реплаем
                if chat_message.reply_to_tg_message_id:
                    result = await session.execute(
                        select(Message).filter_by(
                            tg_message_id=chat_message.reply_to_tg_message_id,
                            chat_id=chat_message.chat_id
                        )
                    )
                    replied_message = result.scalar_one_or_none()

                    if replied_message:
                        result = await session.execute(
                            select(User).filter_by(id=replied_message.user_id)
                        )
                        replied_user = result.scalar_one_or_none()
                        replied_username = replied_user.tg_username if replied_user and replied_user.tg_username else "Неизвестный"

                        # Обрабатываем тип replied-сообщения
                        if replied_message.type == "text" or (
                                replied_message.content and replied_message.content not in ["[photo]", "[sticker]",
                                                                                            "[video]", "[voice]",
                                                                                            "[audio]", "[document]",
                                                                                            "[animation]",
                                                                                            "[video_note]", "[dice]",
                                                                                            "[poll]"]):
                            # Проверяем content на None перед использованием len()
                            short_text = replied_message.content[:80] + "..." if replied_message.content and len(
                                replied_message.content) > 80 else replied_message.content or "[без текста]"
                            reply_desc = f"сообщение \"{short_text}\""
                        else:
                            reply_desc = type_map.get(replied_message.type, f"что-то странное ({replied_message.type})")

                        summary.append(
                            f"{chat_message.timestamp} юзер '{username}' ответил \"{chat_message.content}\" на {reply_desc} от юзера '{replied_username}'"
                        )
                    else:
                        print("⚠️ Ошибка: Не найдено сообщение, на которое идет ответ!")
                        summary.append(
                            f"{chat_message.timestamp} юзер '{username}' ответил \"{chat_message.content}\" на неизвестное сообщение"
                        )
                else:
                    summary.append(
                        f"{chat_message.timestamp} юзер '{username}' {message_desc}"
                    )
            summary.reverse()
            return "\n".join(summary)
    else:
        return "В этом чате пока нет сообщений для отчета."


async def main():
    content = await get_history_listing(tg_chat_id=-1002619036043, limit=16)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())