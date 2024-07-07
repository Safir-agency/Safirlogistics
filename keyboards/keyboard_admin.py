from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton, WebAppInfo
from typing import List

from services.paypal import create_payment
from states.states_admin import AdminCallbackFactory
from states.states_client import ClientCallbackFactory
from lexicon.lexicon_admin import LEXICON_BUTTON_STATISTICS, LEXICON_LOOK_FOR_CLIENT, LOOK_FOR_ORDER_NOT_PAID, \
    LEXICON_STATISTIC_CLIENTS_TELEGRAM, LEXICON_STATISTIC_CLIENTS_EXCEL, LEXICON_STATISTIC_BY_CLIENT_TG, \
    LEXICON_STATISTIC_BY_CLIENT_EXCEL, LEXICON_BY_LAST_7_DAYS, LEXICON_BY_LAST_30_DAYS, LEXICON_LAST_HALF_YEAR, \
    LEXICON_LAST_1_YEAR, LEXICON_ANSWER_TO_CLIENT, \
    LEXICON_ADD_5_CLIENTS, LEXICON_BACK_TO_MENU, LEXICON_BACK_TO_PREVIOUS_CLIENTS, LEXICON_GIVE_CLIENT_PAYMENT_INFO


def set_admin_menu(lang) -> InlineKeyboardMarkup:
    statistics_text = LEXICON_BUTTON_STATISTICS.get(lang, 'en')
    look_for_client_text = LEXICON_LOOK_FOR_CLIENT.get(lang, 'en')
    look_for_order_not_paid_text = LOOK_FOR_ORDER_NOT_PAID.get(lang, 'en')
    receipt_text = LEXICON_GIVE_CLIENT_PAYMENT_INFO.get(lang, 'en')
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=statistics_text,
                                     callback_data=AdminCallbackFactory(action="statistics").pack()),
                InlineKeyboardButton(text=look_for_client_text,
                                     callback_data=AdminCallbackFactory(action="look_for_client").pack())
            ],
            [
                InlineKeyboardButton(text=receipt_text,
                                     callback_data=AdminCallbackFactory(action="receipt_text").pack())
            ]
            # [
            #     InlineKeyboardButton(text=look_for_order_not_paid_text,
            #                          callback_data=AdminCallbackFactory(action="look_for_order_not_paid").pack()),
            # ]
        ]
    )
    return keyboard


def add_five_clients(lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_ADD_5_CLIENTS.get(lang, 'en'),
                                     callback_data=AdminCallbackFactory(action="add_five_clients").pack())
            ],
            [
                InlineKeyboardButton(text="🔙 Back",
                                     callback_data=AdminCallbackFactory(action="back_to_admin_menu").pack())
            ]
        ]
    )
    return keyboard


def set_choose_5_clients(clients: List[str], lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=client,
                                                  callback_data=AdminCallbackFactory(action="choose_5_clients",
                                                                                     client_id=client).pack())]
                            for client in clients[:5]
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_ADD_5_CLIENTS.get(lang, 'en'),
                                                  callback_data=AdminCallbackFactory(
                                                      action="add_five_clients").pack())],
                            [InlineKeyboardButton(text=LEXICON_BACK_TO_MENU.get(lang, 'en'),
                                                  callback_data=AdminCallbackFactory(
                                                      action="back_to_admin_menu_clients").pack()),
                             InlineKeyboardButton(text=LEXICON_BACK_TO_PREVIOUS_CLIENTS.get(lang, 'en'),
                                                  callback_data=AdminCallbackFactory(
                                                      action="back_to_previous_clients").pack())]
                        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def set_statistics_menu(lang) -> InlineKeyboardMarkup:
    statistics_by_clients_tg = LEXICON_STATISTIC_CLIENTS_TELEGRAM.get(lang, 'en')
    statistics_by_clients_excel = LEXICON_STATISTIC_CLIENTS_EXCEL.get(lang, 'en')
    statistics_by_client_tg = LEXICON_STATISTIC_BY_CLIENT_TG.get(lang, 'en')
    statistics_by_client_excel = LEXICON_STATISTIC_BY_CLIENT_EXCEL.get(lang, 'en')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=statistics_by_clients_tg,
                                     callback_data=AdminCallbackFactory(action="statistics_by_clients_tg").pack())
                ],
            [
                InlineKeyboardButton(text=statistics_by_clients_excel,
                                     callback_data=AdminCallbackFactory(action="statistics_by_clients_excel").pack())
            ],
            [
                InlineKeyboardButton(text=statistics_by_client_tg,
                                     callback_data=AdminCallbackFactory(action="statistics_by_client_tg").pack())
                ],
            [
                InlineKeyboardButton(text=statistics_by_client_excel,
                                     callback_data=AdminCallbackFactory(action="statistics_by_client_excel").pack())
            ],
            [
                InlineKeyboardButton(text="🔙 Back",
                                     callback_data=AdminCallbackFactory(action="back_to_admin_menu").pack())
            ]
        ]
    )

    return keyboard

def set_choose_client_for_receipt(clients: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=client,
                                  callback_data=AdminCallbackFactory(
                                      action="set_choose_client_for_receipt", client_id=client).pack())]
            for client in clients
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def set_choose_client(clients: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=client,
                                  callback_data=AdminCallbackFactory(action="choose_client", client_id=client).pack())]
            for client in clients
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def set_choose_client_phone(clients: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=client,
                                  callback_data=AdminCallbackFactory(action="choose_client_phone",
                                                                     client_id=client).pack())]
            for client in clients
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

#
# def set_orders_not_paid_menu(lang) -> InlineKeyboardMarkup:
#     by_7_days = LEXICON_BY_LAST_7_DAYS.get(lang, 'en')
#     by_30_days = LEXICON_BY_LAST_30_DAYS.get(lang, 'en')
#     by_last_half_year = LEXICON_LAST_HALF_YEAR.get(lang, 'en')
#     by_last_1_year = LEXICON_LAST_1_YEAR.get(lang, 'en')
#
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(text=by_7_days,
#                                      callback_data=AdminCallbackFactory(action="orders_by_7_days_not_paid").pack()),
#                 InlineKeyboardButton(text=by_30_days,
#                                      callback_data=AdminCallbackFactory(action="orders_by_30_days_not_paid").pack())
#             ],
#             [
#                 InlineKeyboardButton(text=by_last_half_year,
#                                      callback_data=AdminCallbackFactory(action="orders_by_last_half_year_not_paid").pack()),
#                 InlineKeyboardButton(text=by_last_1_year,
#                                      callback_data=AdminCallbackFactory(action="orders_by_last_1_year_not_paid").pack())
#             ],
#             [
#                 InlineKeyboardButton(text="🔙 Back",
#                                      callback_data=AdminCallbackFactory(action="back_to_statistics_not_paid").pack())
#             ]
#         ]
#     )
#
#     return keyboard


# Button for admin to answer to client
def set_answer_to_client(lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_ANSWER_TO_CLIENT.get(lang, 'en'),
                                     callback_data=ClientCallbackFactory(action="answer_to_client").pack())
            ]
        ]
    )
    return keyboard

def set_back_to_menu(lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_BACK_TO_MENU.get(lang, 'en'),
                                     callback_data=AdminCallbackFactory(action="back_to_admin_menu_2").pack())
            ]
        ]
    )
    return keyboard

def payment_button(amount: float) -> InlineKeyboardMarkup:
    approval_url_paypal = create_payment(amount)
    approval_url_pioneer = 'https://login.payoneer.com/'

    buttons = []

    if approval_url_paypal:
        button_paypal = InlineKeyboardButton(
            text="Pay with PayPal",
            web_app=WebAppInfo(url=approval_url_paypal)
        )
        buttons.append([button_paypal])
    else:
        buttons.append([InlineKeyboardButton(text="Error: Unable to create PayPal payment", callback_data="error_paypal")])

    if approval_url_pioneer:
        button_pioneer = InlineKeyboardButton(
            text="Pay with Payoneer",
            web_app=WebAppInfo(url=approval_url_pioneer)
        )
        buttons.append([button_pioneer])
    else:
        buttons.append([InlineKeyboardButton(text="Error: Unable to create Pioneer payment", callback_data="error_pioneer")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

