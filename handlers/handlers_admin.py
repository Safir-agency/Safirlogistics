import datetime

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from filters.is_admin import is_admin
from lexicon.lexicon_admin import LEXICON_CHOOSE_ACTION, LEXICON_NO_ACCESS
from states.states_admin import AdminCallbackFactory
from aiogram.types import CallbackQuery, Message

from py_logger import get_logger
from keyboards.keyboard_admin import set_admin_menu, set_statistics_menu, set_orders_menu

logger = get_logger(__name__)

router = Router()


# Handler for "/admin" command
@router.message(Command(commands=["admin"]))
async def process_admin_command(message: Message):
    try:
        if not is_admin(message.from_user.id):
            await message.answer(LEXICON_NO_ACCESS.get(message.from_user.language_code, 'en'))
        else:
            await message.answer(LEXICON_CHOOSE_ACTION.get(message.from_user.language_code, 'en'),
                                 reply_markup=set_admin_menu(message.from_user.language_code))
    except Exception as e:
        logger.error(f'Error in process_admin_command: {e}')


''' Handler for "statistics" action '''


@router.callback_query(AdminCallbackFactory.filter(F.action == "statistics"))
async def process_statistics(callback: CallbackQuery):
    try:
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_statistics_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in process_statistics: {e}')


''' Handler for orders action '''


@router.callback_query(AdminCallbackFactory.filter(F.action == 'look_for_orders_by_quantity'))
async def process_orders(callback: CallbackQuery):
    try:
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_orders_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in process_orders: {e}')


@router.callback_query(AdminCallbackFactory.filter(F.action == "look_for_order_not_paid"))
async def process_orders_not_paid(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_orders_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in process_orders_not_paid: {e}')

@router.callback_query(AdminCallbackFactory.filter(F.action == "look_for_order_paid"))
async def process_orders_paid(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_orders_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in process_orders_paid: {e}')

''' Handler for back actions '''
@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_statistics'))
async def back(callback: CallbackQuery):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")

@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_admin_menu'))
async def back(callback: CallbackQuery):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")