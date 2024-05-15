import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton
from emoji import emojize
from aiogram import types

from states.states_client import ClientCallbackFactory
from config_data.config import Config, load_config


config: Config = load_config('./config_data/.env')
WEB_APP_URL = os.getenv('WEB_APP_URL')

# def set_main_menu(user_id: int) -> InlineKeyboardMarkup:
#     keyboard = types.InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(
#                     text="Submit an application 📝",
#                     callback_data=ClientCallbackFactory(action="form").pack(),
#                     web_app=types.WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}')
#                 )
#             ],
#             [
#                 InlineKeyboardButton(
#                     text="Subscription 💵",
#                     callback_data=ClientCallbackFactory(action="prices").pack()
#                 ),
#                 InlineKeyboardButton(
#                     text="Technical Support 📱",
#                     callback_data=ClientCallbackFactory(action="contacts").pack()
#                 )
#             ]
#         ],
#         resize_keyboard=True,
#     )
#     return keyboard

def set_main_menu(user_id: int) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(
        text="Submit an application 📝",
        web_app=types.WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}')
    )
    button_2 = InlineKeyboardButton(
        text="Subscription 💵",
        callback_data=ClientCallbackFactory(action="prices").pack()
    )
    button_3 = InlineKeyboardButton(
        text="Technical Support 📱",
        callback_data=ClientCallbackFactory(action="contacts").pack()
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button_1],
            [button_2, button_3]
        ]
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


def end_conversation_button() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="End conversation 🚪")]
        ],
        resize_keyboard=True,
    )
    return keyboard


