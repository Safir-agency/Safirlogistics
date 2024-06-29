import asyncio
import base64
import json
import os

import aiohttp
import certifi
import ssl
from fastapi import status
from dotenv import load_dotenv

from py_logger import get_logger

logger = get_logger(__name__)
load_dotenv('./config_data/.env')
MONO_TOKEN = os.getenv('MONO_TOKEN')
WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
REDIRECT_URL = os.getenv('REDIRECT_URL')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET_KEY = os.getenv('PAYPAL_SECRET_KEY')
PAYPAL_BASE_URL = os.getenv('PAYPAL_BASE_URL')

CREATE_INVOICE_PATH = 'https://api.monobank.ua/api/merchant/invoice/create'
HEADERS = {"X-Token": MONO_TOKEN}
WEBHOOK_URL = f"{WEBHOOK_URL}/payment/safir_pay"
WEBHOOK_URL_PAYPAL = f"{WEBHOOK_URL}/payment/safir_paypal"
PAYPAL_SUCCESS_ROUTE = f"{WEBHOOK_URL}/payment/paypal-payment-success"
PAYPAL_CANCEL_ROUTE = f"{WEBHOOK_URL}/payment/paypal-payment-cancel"
ssl_context = ssl.create_default_context(cafile=certifi.where())

GLOBAL_USD_RATE = None


async def set_webhook():
    url = "https://api.monobank.ua/personal/webhook"
    data = {"webHookUrl": WEBHOOK_URL}
    json_data = json.dumps(data)  # Перетворюємо словник на рядок JSON
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=HEADERS, data=json_data, ssl=ssl_context) as response:
            if response.status == status.HTTP_200_OK:
                return await response.json()
            print(f"{response.status=}")
            res = await response.json()
            print(res)
    return {"ok": True}


async def get_usd_rate_mono() -> float:
    """функція отримання поточного курсу валюти USD"""
    logger.info("Start getting USD rate")
    url = "https://api.monobank.ua/bank/currency"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=HEADERS, ssl=ssl_context) as response:
            print(response.status)
            print(response.headers)
            if response.status == status.HTTP_200_OK:
                print(f"Response Status {response.status}")
                data = await response.json()
                for curr in data:
                    if curr.get('currencyCodeA') == 840:
                        usd_rate = round(curr.get("rateSell"), 2)
                        print(f"USD rate is {usd_rate}")
                        global GLOBAL_USD_RATE
                        GLOBAL_USD_RATE = usd_rate
                    return usd_rate
            elif response.status == status.HTTP_429_TOO_MANY_REQUESTS:
                return GLOBAL_USD_RATE
            else:
                if GLOBAL_USD_RATE:
                    return GLOBAL_USD_RATE
                else:
                    await asyncio.sleep(60)
                    return await get_usd_rate_mono()



async def create_invoice_mono(product: dict) -> dict:
    """Функція для стровення інвойсу"""
    logger.info("Start create_invoice")
    body = {
        "amount": int(product["amount"] * 100),
        "ccy": 980,
        "merchantPaymInfo": {
            "reference": str(product["reference"]),
            "destination": product["destination"]},
        "redirectUrl": f"{REDIRECT_URL}?start={str(product['reference'])}",
        "webHookUrl": WEBHOOK_URL,
        "validity": 3600,
        "paymentType": "debit"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=CREATE_INVOICE_PATH, headers=HEADERS, data=json.dumps(body),
                                ssl=ssl_context) as response:
            if response.status == status.HTTP_200_OK:
                print(f"{response.status=}")
                result = await response.json()
                return result
            print(f"{response.status=}")
            result = await response.json()
            print(result)


async def get_paypal_access_token() -> str:
    """функція авторизації в системі paypal"""
    logger.debug("Start get_paypal_access_token")
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    base_cred = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET_KEY}".encode("utf-8")).decode(
        'utf-8')
    payload = 'grant_type=client_credentials'
    HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base_cred}',
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=HEADERS, data=payload, ssl=ssl_context) as response:
            print(f"{response.status=}")
            if response.status == status.HTTP_200_OK:
                result = await response.json()
                return f'{result["token_type"]} {result["access_token"]}'


async def set_paypal_webhook():
    """Функція встановлення вебхука для прийома платежів"""
    logger.info("Start set_paypal_webhook")
    url = f"{PAYPAL_BASE_URL}/v1/notifications/webhooks"
    access_token = await get_paypal_access_token()
    payload = json.dumps({"url": WEBHOOK_URL_PAYPAL, "event_types": [{"name": "*"}]})
    HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': access_token
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=HEADERS, data=payload, ssl=ssl_context) as response:
            print(f"Paypal {response.status=}")
            if response.status == status.HTTP_200_OK:
                result = await response.json()
                print(f"Paypal {result=}")
                return status.HTTP_200_OK
            else:
                result = await response.json()
                print(f"Paypal {result=}")
                return status.HTTP_200_OK


async def create_invoice_paypal(product: dict) -> dict:
    """Функціонал створення інвойсу на оплату Paypal"""
    logger.info("Start create_invoice_paypal")
    access_token = await get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v1/payments/payment"
    HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': access_token
    }
    amount_uah = int(product["amount"])
    usd_rate = await get_usd_rate_mono()
    amount = round(amount_uah / usd_rate, 2)
    data = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [
            {
                "amount": {
                    "total": f"{amount:.2f}",
                    "currency": "USD"
                },
                "description": product["destination"]
            }
        ],
        "redirect_urls": {
            "return_url": PAYPAL_SUCCESS_ROUTE,
            "cancel_url": f"{PAYPAL_CANCEL_ROUTE}/{product['reference']}"
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=HEADERS, data=json.dumps(data), ssl=ssl_context) as response:
            logger.info(f"Paypal {response.status=}")
            result = await response.json()
            logger.debug(f"Paypal {result=}")
            return result
