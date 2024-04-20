from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from create_bot import bot
from database.db_operations import save_user_to_db
from database.models import TelegramUsers

from keyboards.keyboards_client import set_number_btn, set_main_menu

from lexicon.lexicon import LEXICON_START

# from states.states_client import ClientCallbackFactory, ClientStates
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