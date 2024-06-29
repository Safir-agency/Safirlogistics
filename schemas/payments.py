from typing import Optional

from pydantic import BaseModel, EmailStr, Field

"""
{'invoiceId': '2404145J666ZrNRophsn', 'status': 'created', 'amount': 100, 'ccy': 980, 
'createdDate': '2024-04-14T09:36:37Z', 'modifiedDate': '2024-04-14T09:36:37Z', 
'reference': '123', 'destination': 'Order from Telegram Bot'}

"""


class InvoiceRequest(BaseModel):
    invoiceId: str
    status: str
    amount: float
    ccy: str
    createdDate: str
    modifiedDate: str
    reference: str
    destination: str
    lang: str


class PaymentRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    amount: int = Field(ge=1)
    payment_method: str
    lang: str


class PaymentResponse(BaseModel):
    invoiceId: str
    pageUrl: str
