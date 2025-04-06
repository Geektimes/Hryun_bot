#handlers\__init__.py
from aiogram import Dispatcher
from . import basic_handlers

def register_handlers(dp: Dispatcher):
    dp.include_router(basic_handlers.router)
