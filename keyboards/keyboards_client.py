import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton, WebAppInfo
from emoji import emojize
from aiogram import types
from aiogram.utils.web_app import WebAppInitData

from lexicon.lexicon import LEXICON_BUTTON_SUBMIT_AN_APPLICATION, LEXICON_BUTTON_OUR_PRICE, \
    LEXICON_BUTTON_TECHNICAL_SUPPORT, LEXICON_BUTTON_SHARE_NUMBER, LEXICON_BUTTON_BACK_TO_MAIN_MENU, \
    LEXICON_END_CONVERSATION_BUTTON, LEXICON_START_WORK_WITH_US
from services.paypal import create_payment
from states.states_client import ClientCallbackFactory
from config_data.config import Config, load_config

config: Config = load_config('./config_data/.env')
WEB_APP_URL = os.getenv('WEB_APP_URL')


# def set_main_menu(user_id: int, lang) -> ReplyKeyboardMarkup:
#     button_1 = KeyboardButton(
#         text=LEXICON_BUTTON_SUBMIT_AN_APPLICATION.get(lang, 'en'),
#         web_app=WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}'))
#     button_2 = KeyboardButton(
#         text=LEXICON_BUTTON_OUR_PRICE.get(lang, 'en'),
#         callback_data=ClientCallbackFactory(action="prices").pack())
#     button_3 = KeyboardButton(
#         text=LEXICON_BUTTON_TECHNICAL_SUPPORT.get(lang, 'en'),
#         callback_data=ClientCallbackFactory(action="contacts").pack())
#     panel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[button_1], [button_2, button_3]])
#     return panel


# def set_main_menu(user_id: int, lang) -> InlineKeyboardMarkup:
#     button_1 = InlineKeyboardButton(
#         text=LEXICON_BUTTON_SUBMIT_AN_APPLICATION.get(lang, 'en'),
#         web_app=types.WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}')
#     )
#     button_2 = InlineKeyboardButton(
#         text=LEXICON_BUTTON_OUR_PRICE.get(lang, 'en'),
#         callback_data=ClientCallbackFactory(action="prices").pack()
#     )
#     button_3 = InlineKeyboardButton(
#         text=LEXICON_BUTTON_TECHNICAL_SUPPORT.get(lang, 'en'),
#         callback_data=ClientCallbackFactory(action="contacts").pack()
#     )
#     button_4 = InlineKeyboardButton(
#         text="Pay",
#         callback_data=ClientCallbackFactory(action="pay").pack()
#     )
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [button_1],
#             [button_2, button_3],
#             [button_4]
#         ]
#     )
#     return keyboard


def set_main_menu(user_id: int, lang) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(
        text=LEXICON_START_WORK_WITH_US.get(lang, 'en'),
        callback_data=ClientCallbackFactory(action="start_work_with_us").pack()
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


def form_button(user_id: int, lang) -> ReplyKeyboardMarkup:
    button_1 = KeyboardButton(
        text=LEXICON_BUTTON_SUBMIT_AN_APPLICATION.get(lang, 'en'),
        web_app=WebAppInfo(url=f'{WEB_APP_URL}/form?userId={user_id}'))
    panel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[button_1]])

    return panel


def set_number_btn(lang) -> ReplyKeyboardMarkup:
    keyboards = KeyboardButton(text=LEXICON_BUTTON_SHARE_NUMBER.get(lang, 'en'), request_contact=True)
    panel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, keyboard=[[keyboards]])
    return panel


def set_back_button(lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_BUTTON_BACK_TO_MAIN_MENU.get(lang, 'en'),
                                     callback_data=ClientCallbackFactory(
                                         action="back").pack())
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


def paypal_button(amount: float, lang) -> InlineKeyboardMarkup:
    approval_url = create_payment(amount)
    if approval_url:
        button_4 = InlineKeyboardButton(
            text="Pay with PayPal",
            web_app=WebAppInfo(url=approval_url)
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_4]])
        return keyboard
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Error: Unable to create payment", callback_data="error")]
        ])
