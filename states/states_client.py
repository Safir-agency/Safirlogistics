from typing import Optional

from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData


class ClientCallbackFactory(CallbackData, prefix="client"):
    action: str


class ClientStates(StatesGroup):
    waiting_for_links = State()
    waiting_for_phone_number = State()
    waiting_for_location = State()
    waiting_for_ts_message = State()