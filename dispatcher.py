from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from handlers.handlers_admin import router as admin_router
from handlers.client_handlers import router as command_router

storage = MemoryStorage()
dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)

dp.include_router(command_router)
dp.include_router(admin_router)
