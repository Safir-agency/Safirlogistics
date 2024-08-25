from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State

class AdminCallbackFactory(CallbackData, prefix="admin"):
    action: str
    client_id: Optional[str] = None
    context: Optional[str] = None
    subscription_id: Optional[int] = None
    amount: Optional[float] = None

class AdminStates(StatesGroup):
    waiting_for_username_client = State()
    waiting_for_more_clients_info = State()
    waiting_for_asin = State()
    waiting_for_username_client_to_change_amount = State()
