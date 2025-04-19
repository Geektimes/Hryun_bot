# handlers/__init__.py
from aiogram import Dispatcher
from .basic_handlers import rate_limited_router, router

def register_handlers(dp: Dispatcher):
    dp.include_router(rate_limited_router)
    dp.include_router(router)

