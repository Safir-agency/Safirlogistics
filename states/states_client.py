from typing import Optional

from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData


class ClientCallbackFactory(CallbackData, prefix="client"):
    action: str


class ClientStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_amount_due = State()
    waiting_for_asin = State()

class TechSupportStates(StatesGroup):
    waiting_for_message_from_client = State()
    waiting_for_message_from_tech_support = State()
    wait_for_new_message = State()
    waiting_for_screenshot = State()

