import json
import os

import aiohttp
from fastapi import APIRouter, status, Request, Path
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from database.db_operations import save_client, save_invoice, db_check_is_fresh_payment, change_invoice_status, \
    get_client_id_by_invoice_id
from schemas.payments import InvoiceRequest, PaymentResponse, PaymentRequest
from services.payments import create_invoice_mono, create_invoice_paypal, get_paypal_access_token, ssl_context
from py_logger import get_logger
from dotenv import load_dotenv

logger = get_logger(__name__)

router = APIRouter(tags=["payment"], prefix='/payment')
templates = Jinja2Templates(directory="templates")

load_dotenv('./config_data/.env')

MONO_TOKEN = os.getenv('MONO_TOKEN')
WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
REDIRECT_URL = os.getenv('REDIRECT_URL')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET_KEY = os.getenv('PAYPAL_SECRET_KEY')
PAYPAL_BASE_URL = os.getenv('PAYPAL_BASE_URL')

MONO_DESTINATION_RU = os.getenv('MONO_DESTINATION_RU')
MONO_DESTINATION_UK = os.getenv('MONO_DESTINATION_UK')

@router.get("/safir_pay", status_code=status.HTTP_200_OK)
async def get_answer_to_mono():
    """Функція відповіді на запит Моно про вебхук"""
    logger.info("Mono ask about webhook")
    return {"ok": True}


@router.post("/safir_pay", status_code=status.HTTP_200_OK)
async def invoice_handler(data: InvoiceRequest|dict):
    """Функція обробки інвойсів від Моно"""
    logger.info("Mono invoice_handler started")
    logger.info(f"Data in /safir_pay: {data}")

    if str(data.get("status")) == "success":
        is_fresh_payment = await db_check_is_fresh_payment(invoiceId=data.get("invoiceId"))
        if not is_fresh_payment:
            logger.info(f"Invoice {data.get('invoiceId')} was duplicated - skipping ...")
            return {"ok": True}
        await change_invoice_status(invoiceId=data.get("invoiceId"), status="success")
        print('in success')
    return {"ok": True}


@router.get("/safir_paypal", status_code=status.HTTP_200_OK)
async def get_answer_to_paypal():
    """Функція відповіді на запит Paypal про вебхук"""
    logger.info("Paypal ask about webhook")
    return {"ok": True}


@router.post("/safir_paypal", status_code=status.HTTP_200_OK)
async def paypal_invoice_handler(data: dict):
    """Функція обробки інвойсів від PayPal"""
    logger.info("Paypal paypal_invoice_handler started")
    print(f"{data=}")
    return {"ok": True}


@router.get("/paypal-payment-success", status_code=status.HTTP_200_OK)
async def payment_success(paymentId: str, PayerID: str, request: Request):
    logger.info("Receive data on route payment_success")
    access_token = await get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v1/payments/payment/{paymentId}/execute"
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": access_token,
    }
    data = {
        "payer_id": PayerID
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=HEADERS, data=json.dumps(data), ssl=ssl_context) as response:
            logger.info(f"Paypal {response.status=}")
            result = await response.json()
            logger.debug(f"Paypal {result=}")

    await change_invoice_status(invoiceId=paymentId, status="success")
    user_id = await get_client_id_by_invoice_id(invoiceId=paymentId)
    redirect_url = f"{REDIRECT_URL}?start={user_id}"
    return RedirectResponse(url=redirect_url)


# Handle payment cancel
@router.get("/paypal-payment-cancel/{user_id}", status_code=status.HTTP_200_OK)
def payment_cancel(user_id: int = Path(ge=1)):
    logger.info("Receive data on route payment_cancel")
    redirect_url = f"{REDIRECT_URL}?start={user_id}"
    return RedirectResponse(url=redirect_url)


@router.post("/create_payment", status_code=status.HTTP_200_OK, response_model=PaymentResponse)
async def payment_button_handler(data: PaymentRequest):
    """Функція створення інвойсу для оплати та зберігання користувачів"""
    logger.info("Start payment_button_handler")

    # user_id = await save_client(telegram_id=data.telegram_id, form_id=None)

    # destination = MONO_DESTINATION_UK if data.lang == "uk" else MONO_DESTINATION_RU
    destination = MONO_DESTINATION_RU
    product = {"amount": data.amount, "reference": 1, "destination": destination}
    if data.payment_method == "Monobank":
        invoice_data = await create_invoice_mono(product)
        print(f"{invoice_data=}")
    if data.payment_method == "PayPal":
        paypal_response = await create_invoice_paypal(product)
        payment_url = [obj["href"] for obj in paypal_response['links'] if obj["rel"] == 'approval_url'][0]
        invoice_data = {'invoiceId': paypal_response['id'], 'pageUrl': payment_url}
    await save_invoice(user_id=1, invoice_id=invoice_data["invoiceId"], amount=data.amount,
                       status='created', payment_method=data.payment_method)

    logger.info(f"Received data: {data}")
    return invoice_data
