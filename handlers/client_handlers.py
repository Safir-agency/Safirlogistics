import os

from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from create_bot import bot
from database.db_operations import save_user_to_db, save_application_to_db, save_client_to_db, change_fba_status, \
    change_fbm_status
from database.models import TelegramUsers

from keyboards.keyboards_client import set_number_btn, set_main_menu, set_back_button, end_conversation, \
    choose_fba_or_fbm, set_or_not_set

from lexicon.lexicon import LEXICON_START, LEXICON_TECHNICAL_SUPPORT, LEXICON_END_CONVERSATION, LEXICON_NAME_OF_PRODUCT, \
    LEXICON_CHOOSE_FBM_OR_FBA, LEXICON_ASIN, LEXICON_SET_OR_NOT_SET, LEXICON_NUMBER_OF_UNITS_NOT_SET, \
    LEXICON_NUMBER_OF_SETS, LEXICON_NUMBER_OF_UNITS_IN_SET, \
    LEXICON_PHONE_NUMBER, LEXICON_END_APPLICATION, LEXICON_CHOOSE_AN_ACTION

from states.states_client import ClientCallbackFactory, ClientStates
from emoji import emojize

from utils.utils import custom_validate_phone, fetch_user_ip, fetch_user_location

from config_data.config import Config, load_config

from py_logger import get_logger

logger = get_logger(__name__)

router = Router()
config: Config = load_config('./config_data/.env')
WEB_APP_URL = os.getenv('WEB_APP_URL')


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

        keyboard = set_main_menu(user_id=message.from_user.id)
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

'''Subscription prices'''

@router.callback_query(ClientCallbackFactory.filter(F.action == 'prices'))
async def prices(callback: CallbackQuery, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Prices command from user {callback.from_user.id}")
        # await callback.message.delete()

        await bot.send_photo(
            chat_id=callback.from_user.id,
            photo=BufferedInputFile.from_file(path='./assets/SafirPrepPrice_2024_RU.png'),
            reply_markup=set_back_button()
        )
    except ValueError as e:
        logger.error(f"Error while sending prices message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Back button"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'back'))
async def back(callback: CallbackQuery):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()

        await bot.send_message(chat_id=callback.from_user.id, text=LEXICON_CHOOSE_AN_ACTION.get(
            callback.from_user.language_code, LEXICON_CHOOSE_AN_ACTION['en']
        ), reply_markup=set_main_menu(user_id=callback.from_user.id))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Contact us"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'contacts'))
async def contacts(callback: CallbackQuery, state: FSMContext, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Contacts command from user {callback.from_user.id}")
        # await callback.message.delete()
        await bot.send_message(chat_id=callback.from_user.id,
                               text=LEXICON_TECHNICAL_SUPPORT.get(
                                   callback.from_user.language_code,
                                   LEXICON_TECHNICAL_SUPPORT['en']),
                               reply_markup=end_conversation())

    except ValueError as e:
        logger.error(f"Error while sending contacts message: {e}")
        await callback.answer("An error occurred. Please try again later.")


'''Submit an application'''

@router.callback_query(ClientCallbackFactory.filter(F.action == 'form'))
async def form(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Form command from user {callback.from_user.id}")

        await callback.message.answer(text=LEXICON_NAME_OF_PRODUCT.get(callback.from_user.language_code,
                                                                       LEXICON_NAME_OF_PRODUCT['en']))

        await state.set_state(ClientStates.waiting_for_product_name)

    except ValueError as e:
        logger.error(f"Error while sending form message: {e}")
        await callback.answer("An error occurred. Please try again later.")


# @router.callback_query(ClientCallbackFactory.filter(F.action == 'form'))
# async def form(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"Form command from user {callback.from_user.id}")
#
#         await callback.message.answer(text=LEXICON_NAME_OF_PRODUCT.get(callback.from_user.language_code,
#                                                                        LEXICON_NAME_OF_PRODUCT['en']))
#
#         await state.set_state(ClientStates.waiting_for_product_name)
#
#     except ValueError as e:
#         logger.error(f"Error while sending form message: {e}")
#         await callback.answer("An error occurred. Please try again later.")
#
#
# @router.message(ClientStates.waiting_for_product_name)
# async def add_asin(message: Message, state: FSMContext):
#     try:
#         logger.info(f"Product name from user {message.from_user.id}")
#
#         product_name = message.text
#
#         await state.update_data(product_name=product_name)
#
#         await message.answer(text=LEXICON_ASIN.get(
#             message.from_user.language_code, LEXICON_ASIN['en']))
#
#         await state.set_state(ClientStates.waiting_for_asin)
#
#     except ValueError as e:
#         logger.error(f"Error while sending product name message: {e}")
#         await message.answer("An error occurred. Please try again later.")
#
#
# @router.message(ClientStates.waiting_for_asin)
# async def choose_fbm_or_fba(message: Message, state: FSMContext):
#     try:
#         logger.info(f"Product name from user {message.from_user.id}")
#
#         asin = message.text
#
#         await state.update_data(asin=asin)
#
#         await message.answer(text=LEXICON_CHOOSE_FBM_OR_FBA.get(
#             message.from_user.language_code, LEXICON_CHOOSE_FBM_OR_FBA['en']),
#             reply_markup=choose_fba_or_fbm())
#
#     except ValueError as e:
#         logger.error(f"Error while sending product name message: {e}")
#         await message.answer("An error occurred. Please try again later.")
#
#
# @router.callback_query(ClientCallbackFactory.filter(F.action == 'fba'))
# async def fba(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"FBA command from user {callback.from_user.id}")
#         await state.update_data(client_choice='FBA')
#
#         await bot.send_message(chat_id=callback.from_user.id,
#                                text=LEXICON_SET_OR_NOT_SET.get(
#                                    callback.from_user.language_code,
#                                    LEXICON_SET_OR_NOT_SET['en']),
#                                reply_markup=set_or_not_set())
#
#     except ValueError as e:
#         logger.error(f"Error while sending FBA message: {e}")
#         await callback.answer("An error occurred. Please try again later.")
#
#
# @router.callback_query(ClientCallbackFactory.filter(F.action == 'fbm'))
# async def fbm(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"FBM command from user {callback.from_user.id}")
#         await state.update_data(client_choice='FBM')
#
#         await bot.send_message(chat_id=callback.from_user.id,
#                                text=LEXICON_SET_OR_NOT_SET.get(
#                                    callback.from_user.language_code,
#                                    LEXICON_SET_OR_NOT_SET['en']),
#                                reply_markup=set_or_not_set())
#
#     except ValueError as e:
#         logger.error(f"Error while sending FBM message: {e}")
#         await callback.answer("An error occurred. Please try again later.")
#
#
# @router.callback_query(ClientCallbackFactory.filter(F.action == 'not_set'))
# async def not_set(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"Set command from user {callback.from_user.id}")
#
#         # await callback.message.delete()
#         await bot.send_message(chat_id=callback.from_user.id,
#                                text=LEXICON_NUMBER_OF_UNITS_NOT_SET.get(
#                                    callback.from_user.language_code,
#                                    LEXICON_NUMBER_OF_UNITS_NOT_SET['en']))
#
#         await state.set_state(ClientStates.waiting_for_number_of_units)
#     except ValueError as e:
#         logger.error(f"Error while sending set message: {e}")
#         await callback.answer("An error occurred. Please try again later.")
#
#
# @router.callback_query(ClientCallbackFactory.filter(F.action == 'set'))
# async def set(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"Set command from user {callback.from_user.id}")
#
#         # await callback.message.delete()
#         await bot.send_message(chat_id=callback.from_user.id,
#                                text=LEXICON_NUMBER_OF_SETS.get(
#                                    callback.from_user.language_code,
#                                    LEXICON_NUMBER_OF_SETS['en']))
#
#         await state.set_state(ClientStates.waiting_for_number_of_sets)
#     except ValueError as e:
#         logger.error(f"Error while sending set message: {e}")
#         await callback.answer("An error occurred. Please try again later.")
#
#
# @router.message(ClientStates.waiting_for_number_of_sets)
# async def number_of_sets(message: Message, state: FSMContext):
#     try:
#         logger.info(f"Number of sets from user {message.from_user.id}")
#
#         number_of_sets = message.text
#
#         await state.update_data(number_of_sets=number_of_sets)
#
#         await message.answer(text=LEXICON_NUMBER_OF_UNITS_IN_SET.get(
#             message.from_user.language_code, LEXICON_NUMBER_OF_UNITS_IN_SET['en']))
#
#         await state.set_state(ClientStates.waiting_for_number_of_units)
#
#     except ValueError as e:
#         logger.error(f"Error while sending number of sets message: {e}")
#         await message.answer("An error occurred. Please try again later.")
#
#
# @router.message(ClientStates.waiting_for_number_of_units)
# async def number_of_units(message: Message, state: FSMContext):
#     try:
#         logger.info(f"Number of units from user {message.from_user.id}")
#
#         number_of_units = message.text
#
#         await state.update_data(number_of_units=number_of_units)
#
#         await message.answer(text=LEXICON_PHONE_NUMBER.get(
#             message.from_user.language_code,
#             LEXICON_PHONE_NUMBER['en']),
#             reply_markup=set_number_btn())
#
#         await state.set_state(ClientStates.waiting_for_phone_number)
#
#     except ValueError as e:
#         logger.error(f"Error while sending number of units message: {e}")
#         await message.answer("An error occurred. Please try again later.")
#
#
# @router.message(F.content_type.in_({'contact'}))
# async def process_phone(message: Message, state: FSMContext):
#     try:
#         logger.info(f"Phone callback from user {message.from_user.id}")
#         # await message.delete()
#
#         phone_number = message.contact.phone_number
#
#         await state.update_data(phone_number=phone_number)
#
#         await message.answer(text=LEXICON_END_APPLICATION.get(
#             message.from_user.language_code, LEXICON_END_APPLICATION['en']),
#             reply_markup=set_main_menu(user_id=message.from_user.id))
#
#         data = await state.get_data()
#         logger.info(f"Data: {data}")
#
#         telegram_id = message.from_user.id
#         telegram_username = message.from_user.username
#         logger.info(f"User data: {telegram_id}, {telegram_username}")
#
#         client_choice = data.get('client_choice')
#         form_id = await save_application_to_db(data['product_name'], data['asin'], data['phone_number'], choice=client_choice)
#         if form_id is not None:
#             await save_client_to_db(telegram_id, form_id)
#
#         await state.clear()
#
#     except ValueError as e:
#         logger.error(f"Error while sending phone number message: {e}")
#         await message.answer("An error occurred. Please try again later.")
