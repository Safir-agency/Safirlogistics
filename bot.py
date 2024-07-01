import logging
import os
import sys
from aiogram import Router, Bot, Dispatcher
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram import types
from contextlib import asynccontextmanager
import uvicorn

from bot_init import bot
from dispatcher import dp

from database.models import create_tables, do_peewee_migration
from handlers import handlers_admin, client_handlers
from py_logger import get_logger
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from services.payments import set_webhook, set_paypal_webhook
from routes.payments import router as payment_router

logger = get_logger(__name__)

load_dotenv('./config_data/.env')

API_TOKEN = os.getenv('API_TOKEN')

WEB_APP_URL = os.getenv('WEB_APP_URL')
logger.info(f'WEB_APP_URL: {WEB_APP_URL}')

WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST', '0.0.0.0')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', 8000))
BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret"

logger.info(f'BASE_WEBHOOK_URL: {BASE_WEBHOOK_URL}')
logger.info(f'WEBHOOK_PATH: {WEBHOOK_PATH}')
logger.info(f'WEB_SERVER_HOST: {WEB_SERVER_HOST}')
logger.info(f'WEB_SERVER_PORT: {WEB_SERVER_PORT}')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
    await set_webhook()
    await set_paypal_webhook()
    yield
    await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)
logger.info("App is starting...")

app.include_router(payment_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(request: Request):
    return {"ok": True}


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    logger.debug("Bot received data from Telegram Server")
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


def main():
    logger.info('Starting bot...')

    # Create db tables
    create_tables()
    logger.info('Tables created...')

    uvicorn.run('bot:app', host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, reload=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()