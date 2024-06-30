import os

from aiogram import Bot, types

from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv
from py_logger import get_logger

logger = get_logger(__name__)

load_dotenv('./config_data/.env')
TG_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))







