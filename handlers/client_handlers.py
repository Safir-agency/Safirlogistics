import asyncio
import json
import os
import pytz
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendVideo, SendAudio, SendVoice, SendPhoto, SendDocument
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from emoji import emojize
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import font_manager
import pandas as pd
from aiogram.types import FSInputFile

from bot_init import bot
from config_data.config import Config, load_config
from database.db_operations import save_user_to_db, save_user_tech_support, save_filled_form_to_db, save_payment, \
    get_client_id_by_telegram_id, get_form_id_by_asin
from database.models import TelegramUsers
from keyboards.keyboard_admin import set_service_price, enter_asin
from keyboards.keyboards_client import set_main_menu, set_back_button, \
    end_conversation_button, paypal_button, form_button, support_keyboard
from lexicon.lexicon import LEXICON_START, LEXICON_TECHNICAL_SUPPORT, LEXICON_END_CONVERSATION, \
    LEXICON_CHOOSE_AN_ACTION, LEXICON_MESSAGE_SEND, \
    LEXICON_AMOUNT_TO_PAY, LEXICON_RULES_START_WORK_WITH_US, LEXICON_THANKS_FOR_FORM, LEXICON_PLS_PIN_SCREENSHOT, \
    LEXICON_SCREENSHOT_SENDED, LEXICON_PLS_PIN_PHOTO_OR_DOC
from lexicon.lexicon_admin import LEXICON_USER_MESSAGE, LEXICON_PLS_ANSWER, LEXICON_FORM_INFO_FROM_CLIENT, \
    LEXICON_USER_SEND_SCREENSHOT, LEXICON_DB_PRICE_UPDATED
from py_logger import get_logger
from services.paypal import create_payment
from states.states_admin import AdminStates
from states.states_client import ClientCallbackFactory, ClientStates, TechSupportStates

logger = get_logger(__name__)

router = Router()
config: Config = load_config('./config_data/.env')
WEB_APP_URL = os.getenv('WEB_APP_URL')

tech_support_chat_id = os.getenv('CHAT_ID')

admin = os.getenv('ADMIN_IDS')

''' Client main menu '''
font_path = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
dejavu_font_path = next((path for path in font_path if 'dejavusans' in path.lower()), None)


def create_form_image(form_data, username, current_date):
    data = {
        "Field": ["Product Name", "ASIN", "Phone Number", "FBA", "FBM", "Number of Units", "SET",
                  "Number of Units in SET", "Number of SETs", "Comment"],
        "Value": [
            form_data.get("product_name", "No"),
            form_data.get("ASIN", "No"),
            form_data.get("phone_number", "No"),
            "Yes" if form_data.get("FBA", False) else "No",
            "Yes" if form_data.get("FBM", False) else "No",
            form_data.get("FBA_details", {}).get("number_of_units", "0") if form_data.get("FBA",
                                                                                          False) else form_data.get(
                "FBM_details", {}).get("number_of_units", "0"),
            "Yes" if (form_data.get("FBA", False) and form_data.get("FBA_details", {}).get("SET", False)) or (
                    form_data.get("FBM", False) and form_data.get("FBM_details", {}).get("SET", False)) else "No",
            form_data.get("FBA_details", {}).get("number_of_units_in_set", "0") if form_data.get("FBA",
                                                                                                 False) else form_data.get(
                "FBM_details", {}).get("number_of_units_in_set", "0"),
            form_data.get("FBA_details", {}).get("number_of_sets", "0") if form_data.get("FBA",
                                                                                         False) else form_data.get(
                "FBM_details", {}).get("number_of_sets", "0"),
            form_data.get("FBA_details", {}).get("comment", "No comment") if form_data.get("FBA",
                                                                                           False) else form_data.get(
                "FBM_details", {}).get("comment", "No comment")
        ]
    }

    df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(8, 10))
    ax.axis('off')

    # Table cell colors
    cell_colors = [["#d0f0c0", "#f0e68c"] for _ in range(len(df))]

    # Create table
    table = ax.table(cellText=df.values, cellLoc='center', loc='center', cellColours=cell_colors, bbox=[0, 0, 1, 1])

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)

    # Make the headers bold and larger
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontsize=14, weight='bold' if key[1] == 0 else 'normal')

    # Add title
    title = f"Form filled by {username} on {current_date}"
    plt.title(title, fontsize=16, weight='bold')

    plt.tight_layout()
    return fig


@router.message(CommandStart())
async def start(message):
    try:
        logger.info(f"Start command from user {message.from_user.id}")
        user_id = message.from_user.id

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

        print(f"User id: {user_id}, username: {username}")

        if message.video:
            logger.info(f"Video message from user {message.from_user.id}")
            file_id = message.video.file_id
            file_type = 'video'
            await bot(SendVideo(chat_id=admin, video=file_id, caption=message.caption))
        if message.audio:
            logger.info(f"Audio message from user {message.from_user.id}")
            file_id = message.audio.file_id
            file_type = 'audio'
            await bot(SendAudio(chat_id=admin, audio=file_id, caption=message.caption))
        if message.voice:
            logger.info(f"Voice message from user {message.from_user.id}")
            file_id = message.voice.file_id
            file_type = 'voice'
            await bot(SendVoice(chat_id=admin, voice=file_id, caption=message.caption))
        if message.photo:
            logger.info(f"Photo message from user {message.from_user.id}")
            file_id = message.photo[-1].file_id
            file_type = 'photo'
            await bot(SendPhoto(chat_id=admin, photo=file_id, caption=message.caption))
        if message.document:
            logger.info(f"Document message from user {message.from_user.id}")
            file_id = message.document.file_id
            file_type = 'document'
            await bot(SendDocument(chat_id=admin, document=file_id, caption=message.caption))
        else:
            await bot.send_message(chat_id=admin,
                                   text=LEXICON_USER_MESSAGE.get(
                                       message.from_user.language_code,
                                       LEXICON_USER_MESSAGE['en']).format(
                                       user=message.from_user.username,
                                       message=message.text),
                                   reply_markup=support_keyboard(lang=message.from_user.language_code))

        await message.answer(LEXICON_MESSAGE_SEND.get(
            message.from_user.language_code,
            LEXICON_MESSAGE_SEND['en']))

        await save_user_tech_support(telegram_id=user_id, message=message.text, file_type=file_type, file_id=file_id)
        await state.update_data(user_id=user_id)

        data = await state.get_data()
        logger.info(f"Data in tech_support_conversation: {data}")

    except ValueError as e:
        logger.error(f"Error while sending tech support message: {e}")
        await message.answer("An error occurred. Please try again later.")


"""Answer from technical support """


@router.callback_query(ClientCallbackFactory.filter(F.action == 'answer_to_client'))
async def answer_to_client_btn(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Answer to client command from user {callback.from_user.id}")

        data = await state.get_data()
        logger.info(f"Data in answer_to_client_btn: {data}")
        user_id = data.get('user_id')

        if user_id is None:
            logger.error("Data not saved. Please try again.")
            return
        else:
            logger.info(f"Data in answer_to_client_btn: {user_id}")

        logger.info(
            f"Setting state to waiting_for_message_from_tech_support for user {support_keyboard(lang=callback.from_user.language_code)}")

        await bot.send_message(chat_id=admin, text=LEXICON_PLS_ANSWER.get(
            callback.from_user.language_code, LEXICON_PLS_ANSWER['en']))

        await state.set_state(TechSupportStates.waiting_for_message_from_tech_support)

    except ValueError as e:
        logger.error(f"Error while sending answer to client message: {e}")
        await callback.answer("An error occurred. Please try again later.")


@router.message(TechSupportStates.waiting_for_message_from_tech_support)
async def answer_to_client(message: Message, state: FSMContext):
    try:
        logger.info(f"Answer to client message from user {message.from_user.id}")

        data = await state.get_data()
        if not data:
            logger.error("Data not saved. Please try again.")
            return
        user_id = data.get('user_id')
        logger.info(f"Data in answer_to_client: {data}")

        await bot.send_message(chat_id=user_id, text=message.text)
        await message.answer("Message sent to the client.")
        # await state.clear()

    except ValueError as e:
        logger.error(f"Error while sending answer to client message: {e}")
        await message.answer("An error occurred. Please try again later.")


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


"""Payment"""

# @router.callback_query(ClientCallbackFactory.filter(F.action == 'pay'))
# async def waiting_for_amount(callback: CallbackQuery, state: FSMContext):
#     try:
#         logger.info(f"Payment command from user {callback.from_user.id}")
#
#         await callback.answer()
#         await callback.message.answer(LEXICON_AMOUNT_TO_PAY.get(
#             callback.from_user.language_code,
#             LEXICON_AMOUNT_TO_PAY['en']))
#
#         await state.set_state(ClientStates.waiting_for_amount)
#
#     except Exception as e:
#         logger.error(f"Error while processing payment: {e}")
#         await callback.answer("An error occurred. Please try again later.")


# @router.message(ClientStates.waiting_for_amount)
# async def payment(message: types.Message, state: FSMContext):
#     try:
#         logger.info(f"Processing payment for user {message.from_user.id}")
#         amount = float(message.text)
#         if amount <= 0:
#             await message.answer("Please enter a valid amount.")
#             return
#
#         approval_url = create_payment(amount)
#
#         keyboard = paypal_button(amount=amount, lang=message.from_user.language_code)
#         if approval_url:
#             await message.answer("Click the button below to pay with PayPal.", reply_markup=keyboard)
#         else:
#             await message.answer("Error: Unable to create payment.")
#
#         await state.clear()
#
#     except ValueError as e:
#         logger.error(f"Error while processing payment: {e}")
#         await message.answer("An error occurred. Please try again later.")


"""Submit an application"""


@router.callback_query(ClientCallbackFactory.filter(F.action == 'start_work_with_us'))
async def submit_an_application(callback: CallbackQuery):
    try:
        logger.info(f"Submit an application command from user {callback.from_user.id}")
        # await callback.message.delete()

        keyboard = form_button(user_id=callback.from_user.id, lang=callback.from_user.language_code)

        start_work = await callback.message.answer(LEXICON_RULES_START_WORK_WITH_US.get(
            callback.from_user.language_code,
            LEXICON_RULES_START_WORK_WITH_US['en']),
            reply_markup=keyboard)

    except ValueError as e:
        logger.error(f"Error while sending submit an application message: {e}")
        await callback.answer("An error occurred. Please try again later.")


@router.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message, state: FSMContext):
    try:
        logger.info(f"Received data from web app: {message.web_app_data}")

        web_app_data = message.web_app_data
        data = web_app_data.data

        # Deserialize the JSON data
        data_dict = json.loads(data)
        form_data = data_dict.get("formData", {})

        product_name = form_data.get("product_name")
        ASIN = form_data.get("ASIN")
        phone_number = form_data.get("phone_number", "")
        FBA = form_data.get("FBA", False)
        FBM = form_data.get("FBM", False)

        if FBA:
            details = form_data.get("FBA_details", {})
        elif FBM:
            details = form_data.get("FBM_details", {})
        else:
            details = {}

        number_of_units = details.get("number_of_units", 0)
        SET = details.get("SET", False)
        number_of_units_in_set = details.get("number_of_units_in_set", 0)
        number_of_sets = details.get("number_of_sets", 0)
        comment = details.get("comment", "")

        telegram_id = message.from_user.id
        print(f"User id: {telegram_id}")
        await bot.send_message(text=LEXICON_THANKS_FOR_FORM.get(
            message.from_user.language_code,
            LEXICON_THANKS_FOR_FORM['en']),
            chat_id=telegram_id,
            reply_markup=set_main_menu(telegram_id, message.from_user.language_code))
        logger.info(f"User {telegram_id} sent data from web app: {data}")

        await bot.send_message(chat_id=tech_support_chat_id,
                               text=LEXICON_FORM_INFO_FROM_CLIENT.get(
                                   message.from_user.language_code,
                                   LEXICON_FORM_INFO_FROM_CLIENT['en']).format(
                                   username=message.from_user.username))

        await save_filled_form_to_db(product_name=product_name,
                                     ASIN=ASIN, SET=SET, NOT_SET=not SET,
                                     number_of_sets=number_of_sets,
                                     number_of_units_in_set=number_of_units_in_set,
                                     number_of_units=number_of_units, FBA=FBA,
                                     FBM=FBM, phone_number=phone_number,
                                     comment=comment)
        print(f"Form data: {form_data}")

        client_id = await get_client_id_by_telegram_id(telegram_id)
        print(f"Client id: {client_id}")

        form_id = await get_form_id_by_asin(ASIN)

        await save_payment(
            client_id=client_id,
            form_id=form_id,
            amount_due=0,
            amount_paid=0,
            is_paid=False,
        )

        # Create and send the image
        image = create_form_image(form_data, message.from_user.username,
                                  datetime.now(pytz.timezone("Europe/Kiev")).strftime("%Y-%m-%d"))
        image_path = f'filled_forms/form_{message.from_user.username}_{datetime.now(pytz.timezone("Europe/Kiev")).strftime("%Y-%m-%d_%H-%M-%S")}.png'
        image.savefig(image_path)

        await bot.send_photo(chat_id=tech_support_chat_id, photo=FSInputFile(image_path),
                             reply_markup=enter_asin(lang=message.from_user.language_code))

    except Exception as e:
        logger.error(f"Error while processing web app data: {e}")
        await message.answer("An error occurred. Please try again later.")


@router.callback_query(ClientCallbackFactory.filter(F.action == 'send_screenshot'))
async def send_screenshot(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Send screenshot command from user {callback.from_user.id}")

        await callback.message.answer(LEXICON_PLS_PIN_SCREENSHOT.get(
            callback.from_user.language_code,
            LEXICON_PLS_PIN_SCREENSHOT['en']))

        await state.set_state(TechSupportStates.waiting_for_screenshot)

    except ValueError as e:
        logger.error(f"Error while sending screenshot message: {e}")
        await callback.answer("An error occurred. Please try again later.")


@router.message(TechSupportStates.waiting_for_screenshot)
async def screenshot(message: Message, state: FSMContext):
    try:
        logger.info(f"Screenshot message from user {message.from_user.id}")

        user_id = message.from_user.id
        username = message.from_user.username
        file_id = None
        file_type = None

        if message.photo:
            logger.info(f"Photo message from user {message.from_user.id}")
            file_id = message.photo[-1].file_id
            file_type = 'payment_screenshot'
            await bot.send_message(chat_id=admin, text=LEXICON_USER_SEND_SCREENSHOT.get(
                message.from_user.language_code,
                LEXICON_USER_SEND_SCREENSHOT['en']).format(user=username))
            await bot(SendPhoto(chat_id=admin, photo=file_id, caption=message.caption))
            await message.answer(LEXICON_SCREENSHOT_SENDED.get(
                message.from_user.language_code,
                LEXICON_SCREENSHOT_SENDED['en']))
        if message.document:
            logger.info(f"Document message from user {message.from_user.id}")
            file_id = message.document.file_id
            file_type = 'payment_screenshot'
            await bot.send_message(chat_id=admin, text=LEXICON_USER_SEND_SCREENSHOT.get(
                message.from_user.language_code,
                LEXICON_USER_SEND_SCREENSHOT['en']).format(user=username))
            await bot(SendDocument(chat_id=admin, document=file_id, caption=message.caption))
            await message.answer(LEXICON_SCREENSHOT_SENDED.get(
                message.from_user.language_code,
                LEXICON_SCREENSHOT_SENDED['en']))
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=LEXICON_PLS_PIN_PHOTO_OR_DOC.get(
                                       message.from_user.language_code,
                                       LEXICON_PLS_PIN_PHOTO_OR_DOC['en']))
            await state.set_state(TechSupportStates.waiting_for_screenshot)

        # await save_user_tech_support(telegram_id=user_id, message=message.text, file_type=file_type, file_id=file_id)
        # await state.update_data(user_id=user_id)
        #
        # data = await state.get_data()
        # logger.info(f"Data in screenshot: {data}")

    except ValueError as e:
        logger.error(f"Error while sending screenshot message: {e}")
        await message.answer("An error occurred. Please try again later.")
