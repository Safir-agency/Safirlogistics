from typing import Optional

from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData


class ClientCallbackFactory(CallbackData, prefix="client"):
    action: str


class ClientStates(StatesGroup):
    waiting_for_links = State()
    waiting_for_phone_number = State()
    waiting_for_asin = State()
    waiting_for_product_name = State()
    waiting_for_number_of_units = State()
    waiting_for_number_of_sets = State()


class TechSupportStates(StatesGroup):
    waiting_for_message_from_client = State()
    waiting_for_message_from_tech_support = State()

