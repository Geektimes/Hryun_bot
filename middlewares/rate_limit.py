# middlewares/rate_limit.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 1, period: int = 60):
        """
        :param limit: Максимальное количество запросов за период
        :param period: Период в секундах
        """
        self.limit = limit
        self.period = period
        self.user_requests: Dict[int, list] = {}  # Хранит временные метки запросов для каждого пользователя
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Убеждаемся, что событие — это сообщение
        if not isinstance(event, Message):
            logger.debug("Событие не является сообщением, пропускаем rate limit")
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = datetime.now()

        logger.info(f"Проверка rate limit для пользователя {user_id}")

        # Очищаем старые записи
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                timestamp for timestamp in self.user_requests[user_id]
                if current_time - timestamp < timedelta(seconds=self.period)
            ]
        else:
            self.user_requests[user_id] = []

        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.limit:
            logger.info(f"Пользователь {user_id} превысил лимит: {len(self.user_requests[user_id])} запросов")
            await event.answer(
                f"Слишком много запросов! Подождите {self.period} секунд перед следующим запросом."
            )
            return None

        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        logger.info(f"Добавлен запрос для {user_id}. Текущие запросы: {self.user_requests[user_id]}")

        # Передаем управление следующему обработчику
        return await handler(event, data)