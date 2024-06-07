import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton
from emoji import emojize
from aiogram import types

from lexicon.lexicon import LEXICON_BUTTON_SUBMIT_AN_APPLICATION, LEXICON_BUTTON_OUR_PRICE, \
    LEXICON_BUTTON_TECHNICAL_SUPPORT, LEXICON_BUTTON_SHARE_NUMBER, LEXICON_BUTTON_BACK_TO_MAIN_MENU, \
    LEXICON_END_CONVERSATION_BUTTON
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

def set_main_menu(user_id: int, lang) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(
        text=LEXICON_BUTTON_SUBMIT_AN_APPLICATION.get(lang, 'en'),
        web_app=types.WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}')
    )
    button_2 = InlineKeyboardButton(
        text=LEXICON_BUTTON_OUR_PRICE.get(lang, 'en'),
        callback_data=ClientCallbackFactory(action="prices").pack()
    )
    button_3 = InlineKeyboardButton(
        text=LEXICON_BUTTON_TECHNICAL_SUPPORT.get(lang, 'en'),
        callback_data=ClientCallbackFactory(action="contacts").pack()
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [button_1],
            [button_2, button_3]
        ]
    )
    return keyboard


def set_number_btn(lang) -> ReplyKeyboardMarkup:
    keyboards = KeyboardButton(text=LEXICON_BUTTON_SHARE_NUMBER.get(lang, 'en'), request_contact=True)
    panel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[keyboards]])
    return panel


def set_back_button(lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_BUTTON_BACK_TO_MAIN_MENU.get(lang,'en'), callback_data=ClientCallbackFactory(
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


def end_conversation_button(lang) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LEXICON_END_CONVERSATION_BUTTON.get(lang, 'en'))]
        ],
        resize_keyboard=True,
    )
    return keyboard


