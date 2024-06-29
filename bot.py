import logging
import os
import sys
from aiogram import Router
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram import types
from contextlib import asynccontextmanager
import uvicorn

from create_bot import *

from database.models import create_tables, do_peewee_migration
from handlers import handlers_admin, client_handlers
from py_logger import get_logger
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from services.payments import set_webhook, set_paypal_webhook
from routes.payments import router as payment_router

logger = get_logger(__name__)

load_dotenv('./config_data/.env')

API_TOKEN = os.getenv('API_TOKEN')

WEB_APP_URL = os.getenv('WEB_APP_URL')
logger.info(f'WEB_APP_URL: {WEB_APP_URL}')

WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT'))
print('WEB_SERVER_HOST:', WEB_SERVER_HOST,
      'WEB_SERVER_PORT:', WEB_SERVER_PORT)

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret"
BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
logger.info(f'BASE_WEBHOOK_URL: {BASE_WEBHOOK_URL}')
logger.info(f'WEBHOOK_PATH: {WEBHOOK_PATH}')

router = Router()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(url=BASE_WEBHOOK_URL, drop_pending_updates=True)
    await set_webhook()
    # await set_paypal_webhook()  # disable paypal

    yield
    # await bot.delete_webhook()


app = FastAPI(lifespan=lifespan)
logger.info("App is starting..")

app.include_router(payment_router)

origins = [
    "http://localhost:3000",  # Assuming you might be using localhost for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    logger.debug("Bot receive data from Telegram Server")
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


if __name__ == '__main__':
    uvicorn.run('bot:app', host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, reload=True)
