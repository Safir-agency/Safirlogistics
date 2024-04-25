from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton
from emoji import emojize

from states.states_client import ClientCallbackFactory


def set_main_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Submit an application 📝", callback_data=ClientCallbackFactory(
                    action="form").pack())
            ],
            [
                InlineKeyboardButton(text="Subscription 💵", callback_data=ClientCallbackFactory(
                    action="prices").pack()),
                InlineKeyboardButton(text="Technical Support 📱", callback_data=ClientCallbackFactory(
                    action="contacts").pack())
            ]
        ],
        resize_keyboard=True,

    )
    return keyboard


def set_number_btn() -> ReplyKeyboardMarkup:
    keyboards = KeyboardButton(text=f'Share number {(emojize("📱"))}', request_contact=True)
    panel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[keyboards]])
    return panel


def set_back_button() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Menu 🔙", callback_data=ClientCallbackFactory(
                    action="back").pack())
            ]
        ],
        resize_keyboard=True,
    )
    return keyboard


def choose_fba_or_fbm() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="FBA ✅", callback_data=ClientCallbackFactory(
                    action="fba").pack()),
                InlineKeyboardButton(text="FBM ✅", callback_data=ClientCallbackFactory(
                    action="fbm").pack())
            ]
        ],
        resize_keyboard=True,
    )
    return keyboard


def set_or_not_set() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Set ✅", callback_data=ClientCallbackFactory(
                    action="set").pack()),
                InlineKeyboardButton(text="Not set ❌", callback_data=ClientCallbackFactory(
                    action="not_set").pack())
            ]
        ],
        resize_keyboard=True,
    )
    return keyboard


def end_conversation() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="End conversation 🚪", callback_data=ClientCallbackFactory(
                    action="end").pack())
            ]
        ],
        resize_keyboard=True,
    )
    return keyboard

