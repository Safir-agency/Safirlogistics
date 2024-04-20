from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from create_bot import bot
from database.db_operations import save_user_to_db
from database.models import TelegramUsers

from keyboards.keyboards_client import set_number_btn, set_main_menu, set_back_button, end_conversation

from lexicon.lexicon import LEXICON_START, LEXICON_TECHNICAL_SUPPORT, LEXICON_END_CONVERSATION

from states.states_client import ClientCallbackFactory, ClientStates
from emoji import emojize

from utils.utils import custom_validate_phone, fetch_user_ip, fetch_user_location

from config_data.config import Config, load_config

from py_logger import get_logger

logger = get_logger(__name__)

router = Router()
config: Config = load_config('./config_data/.env')

''' Client main menu '''


@router.message(CommandStart())
async def start(message):
    try:
        logger.info(f"Start command from user {message.from_user.id}")
        user_id = message.from_user.id
        # user_ip = await fetch_user_ip(user_id)
        # location = await fetch_user_location(user_ip)

        user_data = {
            'telegram_id': message.from_user.id,
            'telegram_username': message.from_user.username,
            'telegram_fullname': message.from_user.full_name,
            'telegram_lang': message.from_user.language_code
        }

        # Save to db
        user_instance = TelegramUsers(**user_data)
        await save_user_to_db(user_instance)

        keyboard = set_main_menu()
        welcome_text = LEXICON_START.get(message.from_user.language_code, LEXICON_START['en']).format(
            emojize(":smiling_face_with_smiling_eyes:") + emojize(":smiling_face_with_smiling_eyes:"))

        # Create an instance of BufferedInputFile from the file
        photo_input_file = BufferedInputFile.from_file(path='./assets/prev.webp')

        # Send the photo
        await bot.send_photo(chat_id=message.chat.id,
                             photo=photo_input_file,
                             caption=welcome_text,
                             reply_markup=keyboard)

    except ValueError as e:
        logger.error(f"Error while sending start message: {e}")
        await message.answer("An error occurred. Please try again later.")


"""Subscriptions"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'prices'))
async def prices(callback: CallbackQuery, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Prices command from user {callback.from_user.id}")
        await callback.message.delete()

        await bot.send_photo(
            chat_id=callback.from_user.id,
            photo=BufferedInputFile.from_file(path='./assets/SafirPrepPrice2024.png'),
            reply_markup=set_back_button()
        )
    except ValueError as e:
        logger.error(f"Error while sending prices message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Back button"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'back'))
async def back(callback: CallbackQuery, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()
        await bot.send_message(chat_id=callback.from_user.id, text="Main menu", reply_markup=set_main_menu())
    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Contact us"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'contacts'))
async def contacts(callback: CallbackQuery, state: FSMContext, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Contacts command from user {callback.from_user.id}")
        await callback.message.delete()
        await bot.send_message(chat_id=callback.from_user.id,
                               text=LEXICON_TECHNICAL_SUPPORT.get(
                                   callback.from_user.language_code,
                                   LEXICON_TECHNICAL_SUPPORT['en']),
                               reply_markup=end_conversation())

        await state.set_state(ClientStates.waiting_for_ts_message)
    except ValueError as e:
        logger.error(f"Error while sending contacts message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""End conversation"""

@router.callback_query(ClientStates.waiting_for_ts_message, ClientCallbackFactory.filter(F.action == 'end'))
async def end(callback: CallbackQuery, callback_data: ClientCallbackFactory, state: FSMContext):
    try:
        logger.info(f"End command from user {callback.from_user.id}")
        await bot.send_message(chat_id=callback.from_user.id,
                               text=LEXICON_END_CONVERSATION.get(
                                   callback.from_user.language_code,
                                   LEXICON_END_CONVERSATION['en']),
                               reply_markup=set_main_menu())

        await state.clear()
    except ValueError as e:
        logger.error(f"Error while sending end message: {e}")
        await callback.answer("An error occurred. Please try again later.")
