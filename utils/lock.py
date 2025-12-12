# utils\lock.py
from asyncio import Lock


class ChatLocks:
    _locks: dict[int, Lock] = {}

    @classmethod
    def get_lock(cls, chat_id: int) -> Lock:
        if chat_id not in cls._locks:
            cls._locks[chat_id] = Lock()
        return cls._locks[chat_id]

