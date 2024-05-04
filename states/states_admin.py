from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State

class AdminCallbackFactory(CallbackData, prefix="admin"):
    action: str
    context: Optional[str] = None
    subscription_id: Optional[int] = None