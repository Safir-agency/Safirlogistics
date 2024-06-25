import os

from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.methods import SendVideo, SendAudio, SendVoice, SendPhoto, SendDocument

from create_bot import bot
from database.db_operations import save_user_to_db, save_application_to_db, save_client_to_db, change_fba_status, \
    change_fbm_status, save_user_tech_support
from database.models import TelegramUsers
from keyboards.keyboard_admin import set_answer_to_client

from keyboards.keyboards_client import set_main_menu, set_back_button, \
    choose_fba_or_fbm, set_or_not_set, end_conversation_button

from lexicon.lexicon import LEXICON_START, LEXICON_TECHNICAL_SUPPORT, LEXICON_END_CONVERSATION, LEXICON_NAME_OF_PRODUCT, \
    LEXICON_CHOOSE_FBM_OR_FBA, LEXICON_ASIN, LEXICON_SET_OR_NOT_SET, LEXICON_NUMBER_OF_UNITS_NOT_SET, \
    LEXICON_NUMBER_OF_SETS, LEXICON_NUMBER_OF_UNITS_IN_SET, \
    LEXICON_PHONE_NUMBER, LEXICON_END_APPLICATION, LEXICON_CHOOSE_AN_ACTION, LEXICON_MESSAGE_SEND
from lexicon.lexicon_admin import LEXICON_USER_MESSAGE, LEXICON_PLS_ANSWER
from states.states_admin import AdminCallbackFactory

from states.states_client import ClientCallbackFactory, ClientStates, TechSupportStates
from emoji import emojize

from utils.utils import custom_validate_phone, fetch_user_ip, fetch_user_location

from config_data.config import Config, load_config

from py_logger import get_logger

logger = get_logger(__name__)

router = Router()
config: Config = load_config('./config_data/.env')
WEB_APP_URL = os.getenv('WEB_APP_URL')

tech_support_chat_id = os.getenv('CHAT_ID')

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

        keyboard = set_main_menu(user_id=message.from_user.id, lang=message.from_user.language_code)
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

        if callback.from_user.language_code == 'ru':
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=BufferedInputFile.from_file(path='./assets/SafirPrepPrice_2024_RU.png'),
                reply_markup=set_back_button(lang=callback.from_user.language_code)
            )
        if callback.from_user.language_code == 'uk':
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=BufferedInputFile.from_file(path='./assets/SafirPrepPrice_2024_UKR.png'),
                reply_markup=set_back_button(lang=callback.from_user.language_code)
            )
        else:
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=BufferedInputFile.from_file(path='./assets/SafirPrepPrice_2024_EN.png'),
                reply_markup=set_back_button(lang=callback.from_user.language_code)
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
        ), reply_markup=set_main_menu(user_id=callback.from_user.id, lang=callback.from_user.language_code))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Contact us"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'contacts'))
async def contacts(callback: CallbackQuery, state: FSMContext, callback_data: ClientCallbackFactory):
    try:
        logger.info(f"Contacts command from user {callback.from_user.id}")

        await bot.send_message(chat_id=callback.from_user.id,
                               text=LEXICON_TECHNICAL_SUPPORT.get(
                                   callback.from_user.language_code,
                                   LEXICON_TECHNICAL_SUPPORT['en']),
                               reply_markup=end_conversation_button(lang=callback.from_user.language_code))

        await state.set_state(TechSupportStates.waiting_for_message_from_client)

    except ValueError as e:
        logger.error(f"Error while sending contacts message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""Technical support conversation"""


@router.message(TechSupportStates.waiting_for_message_from_client)
async def tech_support_conversation(message: Message, state: FSMContext):
    try:
        logger.info(f"Technical support message from user {message.from_user.id}")

        user_id = message.from_user.id
        username = message.from_user.username
        file_id = None
        file_type = None

        await state.update_data(user_id=user_id, username=username)
        print(f"User id: {user_id}, username: {username}")

        if message.video:
            logger.info(f"Video message from user {message.from_user.id}")
            file_id = message.video.file_id
            file_type = 'video'
            await bot(SendVideo(chat_id=tech_support_chat_id, video=file_id, caption=message.caption))
        if message.audio:
            logger.info(f"Audio message from user {message.from_user.id}")
            file_id = message.audio.file_id
            file_type = 'audio'
            await bot(SendAudio(chat_id=tech_support_chat_id, audio=file_id, caption=message.caption))
        if message.voice:
            logger.info(f"Voice message from user {message.from_user.id}")
            file_id = message.voice.file_id
            file_type = 'voice'
            await bot(SendVoice(chat_id=tech_support_chat_id, voice=file_id, caption=message.caption))
        if message.photo:
            logger.info(f"Photo message from user {message.from_user.id}")
            file_id = message.photo[-1].file_id
            file_type = 'photo'
            await bot(SendPhoto(chat_id=tech_support_chat_id, photo=file_id, caption=message.caption))
        if message.document:
            logger.info(f"Document message from user {message.from_user.id}")
            file_id = message.document.file_id
            file_type = 'document'
            await bot(SendDocument(chat_id=tech_support_chat_id, document=file_id, caption=message.caption))
        else:
            await bot.send_message(chat_id=tech_support_chat_id,
                                   text=LEXICON_USER_MESSAGE.get(
                                       message.from_user.language_code,
                                       LEXICON_USER_MESSAGE['en']).format(
                                       user=message.from_user.username,
                                       message=message.text),
                                   reply_markup=set_answer_to_client(lang=message.from_user.language_code))

        await message.answer(LEXICON_MESSAGE_SEND.get(
            message.from_user.language_code,
            LEXICON_MESSAGE_SEND['en']))

        await save_user_tech_support(telegram_id=user_id, message=message.text, file_type=file_type, file_id=file_id)

    except ValueError as e:
        logger.error(f"Error while sending tech support message: {e}")
        await message.answer("An error occurred. Please try again later.")


"""Answer from technical support """

@router.callback_query(ClientCallbackFactory.filter(F.action == 'answer_to_client'))
async def answer_to_client_btn(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Answer to client command from user {callback.from_user.id}")

        await callback.answer()

        logger.info(f"Setting state to waiting_for_message_from_tech_support for user {callback.from_user.id}")
        await state.set_state(TechSupportStates.waiting_for_message_from_tech_support)
        logger.info(f"State is now: {await state.get_state()}")

        message = LEXICON_PLS_ANSWER.get(callback.from_user.language_code, LEXICON_PLS_ANSWER['en'])
        await bot.send_message(chat_id=tech_support_chat_id, text=message)

    except ValueError as e:
        logger.error(f"Error while sending answer to client message: {e}")
        await callback.answer("An error occurred. Please try again later.")


"""End conversation"""


@router.message(F.text == 'End conversation 🚪')
async def end_conversation(message: Message):
    try:
        logger.info(f"End conversation command from user {message.from_user.id}")
        await message.answer(LEXICON_END_CONVERSATION.get(
            message.from_user.language_code,
            LEXICON_END_CONVERSATION['en']),
            reply_markup=set_main_menu(user_id=message.from_user.id, lang=message.from_user.language_code))
    except ValueError as e:
        logger.error(f"Error while sending end conversation message: {e}")
        await message.answer("An error occurred. Please try again later.")
