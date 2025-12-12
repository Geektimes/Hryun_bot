import redis
import json
import logging
from config import load_config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import User

config = load_config()
logger = logging.getLogger(__name__)

# Инициализация клиента Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True
)


async def load_users_to_redis(db: AsyncSession):
    """Загружает всех пользователей из БД в Redis."""
    try:
        # Получаем всех пользователей из БД
        result = await db.execute(select(User))
        users = result.scalars().all()

        # Очищаем существующие данные в Redis (опционально)
        redis_client.flushdb()

        # Сохраняем пользователей в Redis
        for user in users:
            user_data = {
                "tg_username": user.tg_username,
                "tg_first_name": user.tg_first_name,
                "tg_last_name": user.tg_last_name,
                "tg_user_id": user.tg_user_id,
                "is_bot": user.is_bot
            }
            redis_client.set(f"user:{user.tg_user_id}", json.dumps(user_data))

        logger.info(f"Загружено {len(users)} пользователей в Redis")
    except Exception as e:
        logger.error(f"Ошибка при загрузке пользователей в Redis: {e}", exc_info=True)


async def get_user_from_redis(tg_user_id: int) -> dict:
    """Получает данные пользователя из Redis по tg_user_id."""
    try:
        user_data = redis_client.get(f"user:{tg_user_id}")
        if user_data:
            return json.loads(user_data)
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя из Redis: {e}", exc_info=True)
        return None


async def set_user_to_redis(tg_user_id: int, user_data: dict):
    """Сохраняет данные пользователя в Redis."""
    try:
        redis_client.set(f"user:{tg_user_id}", json.dumps(user_data))
        logger.debug(f"Пользователь {tg_user_id} сохранен в Redis")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя в Redis: {e}", exc_info=True)