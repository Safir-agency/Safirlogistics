import paypalrestsdk
from py_logger import get_logger
from dotenv import load_dotenv
import os

logger = get_logger(__name__)
load_dotenv('./config_data/.env')

# Define constants for PayPal configuration
PAYPAL_MODE = os.getenv('PAYPAL_MODE') # 'sandbox' if using sandbox PayPal account
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID') # 'your_paypal_client_id' if using real PayPal account
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_SECRET_KEY') # 'your_paypal_client_secret' if using real PayPal account
PAYPAL_BASE_URL = os.getenv('PAYPAL_BASE_URL') # 'http://localhost:8000' if running locallyxs

# Initialize PayPal SDK
paypalrestsdk.configure({
    'mode': PAYPAL_MODE,
    'client_id': PAYPAL_CLIENT_ID,
    'client_secret': PAYPAL_CLIENT_SECRET
})

# Define conversation states
# PAYMENT_AMOUNT, PAYMENT_CONFIRMATION = range(2)

def create_payment(amount, currency='USD'):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": f"{PAYPAL_BASE_URL}/execute",
            "cancel_url": f"{PAYPAL_BASE_URL}/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Test Item",
                    "sku": "001",
                    "price": str(amount),
                    "currency": currency,
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(amount),
                "currency": currency
            },
            "description": "This is the payment transaction description."
        }]
    })

    if payment.create():
        logger.info("Payment created successfully")
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                return approval_url
    else:
        logger.error(payment.error)
        return None