import logging
import os
import sys
from aiogram import Router
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram import types

from create_bot import *

from database.models import create_tables
from handlers import handlers_admin, client_handlers
from py_logger import get_logger
from dotenv import load_dotenv

logger = get_logger(__name__)

load_dotenv('./config_data/.env')

API_TOKEN = os.getenv('API_TOKEN')

WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST')
WEB_SERVER_PORT = os.getenv('WEB_SERVER_PORT')
print('WEB_SERVER_HOST:', WEB_SERVER_HOST
      , 'WEB_SERVER_PORT:', WEB_SERVER_PORT)

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret"
BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
print('BASE_WEBHOOK_URL:', f'{BASE_WEBHOOK_URL}{WEBHOOK_PATH}')

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {message.from_user.full_name}!")


@router.message()
async def echo_handler(message: types.Message) -> None:
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Nice try!")


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


# Функция конфигурирования и запуска бота
def main():
    logger.info('Start bot...')
    # Create db tables
    create_tables()
    logger.info('Create tables...')

    # Регистрируем роутер в диспетчере
    dp.include_router(client_handlers.router)
    # dp.include_router(handlers_admin.router)

    dp.startup.register(on_startup)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=3000)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()