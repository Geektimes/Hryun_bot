# middlewares/notificator.py
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message
from typing import Callable, Dict, Any, Awaitable, Optional
from datetime import datetime, timedelta

import logging
from config import load_config
from utils.services import is_user_exists_or_create
from database import User  # Импортируем модель

config = load_config()

logger = logging.getLogger(__name__)

class NotificatorMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_existence: Optional[User] = await is_user_exists_or_create(event)

            if not user_existence[0]:
                text = (f"Подключился новый юзер {'@', user_existence[1].tg_username or 'без username'}, "
                        f"{user_existence[1].tg_first_name or 'без имени'}, "
                        f"ID: {user_existence[1].tg_user_id}")

                logger.debug(f"Событие: {text}")
                await self.notify_owner(event, text)
        else:
            logger.debug("Событие не является сообщением")

        return await handler(event, data)


    async def notify_owner(self, message: Message, msg: str):
        bot: Bot = message.bot
        await bot.send_message(chat_id=config.OWNER_BRO_ID, text=msg)
