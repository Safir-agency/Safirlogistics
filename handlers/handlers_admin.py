from datetime import datetime
import os

import pandas as pd
import matplotlib.pyplot as plt

import pytz
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputFile, FSInputFile
from aiogram.methods import SendVideo, SendAudio, SendVoice, SendPhoto, SendDocument

from database.db_operations import get_clients_telegram_username, get_fba_status, \
    get_fbm_status, get_asin, get_product_name_by_client, get_number_of_units, get_comments, get_set_info, \
    get_not_set_info, get_number_of_sets, number_of_units_in_set, get_all_clients_sorted_by_recent_form, \
    get_last_form_by_client, get_debt_by_client, get_amount_due_by_client, get_amount_paid_by_client, get_amount_due, \
    get_amount_paid, \
    get_clients_not_paid, get_products_not_paid, get_not_paid_orders_by_last_30_days, \
    get_not_paid_orders_by_last_half_year, get_not_paid_orders_by_last_1_year, get_first_order_date_by_client, \
    get_quantity_of_orders_by_client, get_order_number_by_client, sum_units_by_client, get_amount_paid_by_order_number, \
    get_amount_due_by_order_number, get_order_number_by_asin, get_amount_not_paid_by_last_7_days_by_client
from utils.helpers import load_data_to_excel
from filters.is_admin import is_admin
from lexicon.lexicon_admin import LEXICON_CHOOSE_ACTION, LEXICON_NO_ACCESS, LEXICON_SEND_XLSX_BY_ALL_CLIENTS, \
    LEXICON_SEND_XLSX_BY_CLIENT, LEXICON_CHOOSE_CLIENT, LEXICON_SEND_PHOTO_BY_ALL_CLIENTS, LEXICON_SEND_PHOTO_BY_CLIENT, \
    LEXICON_NO_CLIENTS, LEXICON_NEXT_5_CLIENTS, LEXICON_CLIENT_HAS_NO_DEBT, LEXICON_CLIENT_HAS_DEBT, \
    LEXICON_NOT_PAID_LAST_7_DAYS, LEXICON_NOT_PAID_LAST_30_DAYS, LEXICON_NOT_PAID_LAST_HALF_YEAR, \
    LEXICON_NOT_PAID_LAST_1_YEAR, LEXICON_STATISTICS_SEND_SUCCESS, LEXICON_PLEASE_WAIT, LEXICON_NO_NOT_PAID_ORDERS
from states.states_admin import AdminCallbackFactory, AdminStates
from aiogram.types import CallbackQuery, Message
from create_bot import bot
from xlsxwriter import Workbook

from py_logger import get_logger
from keyboards.keyboard_admin import set_admin_menu, set_statistics_menu, set_choose_client, \
    set_choose_client_phone, set_choose_5_clients, set_back_to_menu

logger = get_logger(__name__)

router = Router()
tech_support_chat_id = os.getenv('CHAT_ID')


async def create_statistics_image(df: pd.DataFrame, file_path: str):
    # Вычисляем размеры фигуры
    height_per_row = 0.5
    width_per_col = 1.7
    fig_height = max(4, len(df) * height_per_row)
    fig_width = max(8, len(df.columns) * width_per_col)

    # Создаем фигуру
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')

    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')

    # Настройка внешнего вида таблицы
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    # Настройка стилей ячеек
    cell_colors = ['#d4e157', '#ffeb3b', '#ffee58', '#ffeb3b']  # Цвета для ячеек
    for (i, j), cell in table.get_celld().items():
        cell.set_edgecolor('black')
        if i == 0:
            cell.set_facecolor('#6c757d')  # Цвет заголовка
            cell.set_text_props(weight='bold', color='white')
        elif j == df.columns.get_loc('Amount paid') and df.iloc[i - 1]['Amount paid'] == 0:
            cell.set_facecolor('red')  # Красный цвет для строк с amount_paid = 0
            cell.set_text_props(color='black')
        elif j == df.columns.get_loc('Amount paid') and df.iloc[i - 1]['Amount paid'] < df.iloc[i - 1]['Amount due']:
            cell.set_facecolor('orange')  # Оранжевый цвет для строк с amount_paid < amount_due
            cell.set_text_props(color='black')
        else:
            cell.set_facecolor(cell_colors[i % len(cell_colors)])
            cell.set_text_props(color='black')

    # Сохраняем изображение
    plt.savefig(file_path)
    plt.close()


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


@router.callback_query(AdminCallbackFactory.filter(F.action == "statistics_by_clients_excel"))
async def process_statistics_by_all_clients_excel(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("Starting the creation of statistics by clients in Excel format.")
        await state.clear()
        await callback.message.delete()
        pls_wait_message = await callback.message.answer(
            LEXICON_PLEASE_WAIT.get(callback.from_user.language_code, 'en'))

        orders_dict = {
            'Clients': [],
            'Number of units': [],
            'Amount due': [],
            'Amount paid': [],
            'Registration date': [],
            'Quantity of orders': []
        }

        clients = await get_clients_telegram_username()

        for client in clients:
            orders_number = await get_order_number_by_client(client)
            registration_date = await get_first_order_date_by_client(client)
            quantity_of_orders = await get_quantity_of_orders_by_client(client)
            units = await sum_units_by_client(client)
            total_amount_due = 0
            total_amount_paid = 0

            for order_number in orders_number:
                amount_due = await get_amount_due_by_order_number(order_number)
                total_amount_due += amount_due
                amount_paid = await get_amount_paid_by_order_number(order_number)
                total_amount_paid += amount_paid

            orders_dict['Clients'].append(client)
            orders_dict['Number of units'].append(units)
            orders_dict['Registration date'].append(registration_date.strftime('%d-%m-%Y'))  # Format date
            orders_dict['Quantity of orders'].append(quantity_of_orders)
            orders_dict['Amount due'].append(total_amount_due)
            orders_dict['Amount paid'].append(total_amount_paid)

        df = pd.DataFrame(orders_dict)
        df.drop_duplicates(subset=['Clients'], inplace=True)

        # Specify the filename and create an Excel writer object
        file_name = f"excel_reports/all_clients_statistics_{datetime.now(pytz.timezone('Europe/Kiev')).strftime('%d-%m-%Y')}.xlsx"
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Summary')

        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Summary']

        # Define cell formats
        header_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#D7E4BC', 'border': 1})
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

        # Apply the formats to the columns
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            column_len = max(df[value].astype(str).apply(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, column_len, cell_format)

        # Close the Pandas Excel writer and output the Excel file
        writer.close()

        file = FSInputFile(file_name)

        await pls_wait_message.delete()
        await bot.send_document(chat_id=callback.from_user.id, document=file,
                                reply_markup=set_back_to_menu(callback.from_user.language_code))

        logger.info("Statistics sent successfully.")

    except ValueError as e:
        logger.error(f'Error in process_statistics_by_clients_excel: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == "statistics_by_client_excel"))
async def process_statistics_by_client_excel(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        clients = await get_clients_telegram_username()
        # get unique clients
        clients = list(set(clients))
        await callback.message.answer(LEXICON_CHOOSE_CLIENT.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_client(clients))

        await state.set_state(AdminStates.waiting_for_username_client)

    except Exception as e:
        logger.error(f'Error in process_statistics_by_client_excel: {e}')


@router.callback_query(AdminCallbackFactory.filter(F.action == "choose_client"))
async def process_statistics_by_one_client_excel(callback: CallbackQuery, callback_data: AdminStates,
                                                 state: FSMContext):
    try:
        logger.info("Creating statistics by clients in Excel format")

        await state.clear()
        await callback.message.delete()
        pls_wait_message = await callback.message.answer(
            LEXICON_PLEASE_WAIT.get(callback.from_user.language_code, 'en'))

        orders_dict = {
            'Order №': [],
            'Clients': [],
            'Product name': [],
            'FBA': [],
            'FBM': [],
            'ASIN': [],
            'Number of units': [],
            'Comment': [],
            'Set': [],
            'No set': [],
            'Number of sets': [],
            'Units in set': [],
            'Amount due': [],
            'Amount paid': [],
            'Registration date': [],
        }

        client = callback_data.client_id
        logger.info(f"Client: {client}")

        orders_number = await get_order_number_by_client(client)
        product_names = await get_product_name_by_client(client)
        registration_date = await get_first_order_date_by_client(client)

        for order_number in orders_number:
            for product in product_names:
                asins = await get_asin(product)
                fba = await get_fba_status(product)
                fbm = await get_fbm_status(product)
                number_of_units = await get_number_of_units(product)
                comment = await get_comments(product)
                set_flag = await get_set_info(product)
                no_set = await get_not_set_info(product)
                number_of_sets = await get_number_of_sets(product)
                units_in_set = await number_of_units_in_set(product)

                for asin in asins:
                    amount_due = await get_amount_due(asin)
                    amount_paid = await get_amount_paid(asin)
                    order_num = await get_order_number_by_asin(asin)

                    orders_dict['Order №'].append(order_num[0])
                    orders_dict['Clients'].append(client)
                    orders_dict['Product name'].append(product)
                    orders_dict['FBA'].append('Yes' if fba else 'No')
                    orders_dict['FBM'].append('Yes' if fbm else 'No')
                    orders_dict['ASIN'].append(asin)
                    orders_dict['Number of units'].append(number_of_units)
                    orders_dict['Comment'].append(comment if comment else 'None')
                    orders_dict['Set'].append('Yes' if set_flag else 'No')
                    orders_dict['No set'].append('Yes' if no_set else 'No')
                    orders_dict['Number of sets'].append(number_of_sets if number_of_sets else 0)
                    orders_dict['Units in set'].append(units_in_set if units_in_set else 0)
                    orders_dict['Amount due'].append(amount_due)
                    orders_dict['Amount paid'].append(amount_paid)
                    orders_dict['Registration date'].append(registration_date.strftime('%d-%m-%Y'))

        df = pd.DataFrame(orders_dict)
        df.drop_duplicates(subset=['ASIN', 'Product name'], inplace=True)
        df.sort_values(by='Clients', inplace=True)
        df.sort_values(by='Order №', inplace=True)

        # Specify the filename and create an Excel writer object
        file_name = f"excel_reports/{client}_statistics_{datetime.now(pytz.timezone('Europe/Kiev')).strftime('%d-%m-%Y')}.xlsx"
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Summary')

        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Summary']

        # Define cell formats
        header_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#D7E4BC', 'border': 1})
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

        # Apply the formats to the columns
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            column_len = max(df[value].astype(str).apply(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, column_len, cell_format)

        # Close the Pandas Excel writer and output the Excel file
        writer.close()

        file = FSInputFile(file_name)

        await pls_wait_message.delete()
        await bot.send_document(chat_id=callback.from_user.id, document=file,
                                reply_markup=set_back_to_menu(callback.from_user.language_code))

        logger.info("Statistics sent successfully.")

    except Exception as e:
        logger.error(f'Error in process_statistics_by_client_excel: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == "statistics_by_clients_tg"))
async def process_statistics_by_all_clients_tg(callback: CallbackQuery):
    try:
        logger.info("Creating statistics by clients in Telegram format using matplotlib")
        await callback.message.delete()

        pls_wait_message = await callback.message.answer(
            LEXICON_PLEASE_WAIT.get(callback.from_user.language_code, 'en'))

        orders_dict = {
            'Clients': [],
            'Number of units': [],
            'Amount due': [],
            'Amount paid': []
        }

        clients = await get_clients_telegram_username()

        for client in clients:
            orders_number = await get_order_number_by_client(client)
            units = await sum_units_by_client(client)
            total_amount_due = 0
            total_amount_paid = 0

            for order_number in orders_number:
                amount_due = await get_amount_due_by_order_number(order_number)
                total_amount_due += amount_due
                amount_paid = await get_amount_paid_by_order_number(order_number)
                total_amount_paid += amount_paid

            orders_dict['Clients'].append(client)
            orders_dict['Number of units'].append(units)
            orders_dict['Amount due'].append(total_amount_due)
            orders_dict['Amount paid'].append(total_amount_paid)

        df = pd.DataFrame(orders_dict)
        df.drop_duplicates(subset=['Clients'], inplace=True)
        df.sort_values(by='Clients', inplace=True)
        logger.info("Dataframe created successfully.")

        # Создание и сохранение изображения
        file_path = f'images_reports/all_clients_statistics.png'
        await create_statistics_image(df, file_path)

        # Отправка сообщения
        await bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(file_path),
                                reply_markup=set_back_to_menu(callback.from_user.language_code))
        await pls_wait_message.delete()
        await callback.answer(LEXICON_STATISTICS_SEND_SUCCESS.get(callback.from_user.language_code, 'en'))

    except Exception as e:
        logger.error(f'Error in process_statistics_by_clients_tg: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == "statistics_by_client_tg"))
async def process_statistics_by_client_tg(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()

        clients = await get_clients_telegram_username()
        # get unique clients
        clients = list(set(clients))
        await callback.message.answer(LEXICON_CHOOSE_CLIENT.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_client_phone(clients))

        await state.set_state(AdminStates.waiting_for_username_client)

    except Exception as e:
        logger.error(f'Error in process_statistics_by_client_tg: {e}')


@router.callback_query(AdminCallbackFactory.filter(F.action == "choose_client_phone"))
async def process_statistics_by_one_client_tg(callback: CallbackQuery, callback_data: AdminStates, state: FSMContext):
    try:
        logger.info("Creating statistics by clients in Telegram format using matplotlib")

        pls_wait_message = await callback.message.answer(
            LEXICON_PLEASE_WAIT.get(callback.from_user.language_code, 'en'))

        await callback.message.delete()
        orders_dict = {
            'Order №': [],
            'Clients': [],
            'Product name': [],
            'FBA': [],
            'FBM': [],
            'ASIN': [],
            'Number of units': [],
            'Comment': [],
            'Set': [],
            'No set': [],
            'Number of sets': [],
            'Units in set': [],
            'Amount due': [],
            'Amount paid': [],
            'Registration date': [],
        }

        client = callback_data.client_id
        logger.info(f"Client: {client}")

        orders_number = await get_order_number_by_client(client)
        product_names = await get_product_name_by_client(client)
        registration_date = await get_first_order_date_by_client(client)

        for order_number in orders_number:
            for product in product_names:
                asins = await get_asin(product)
                fba = await get_fba_status(product)
                fbm = await get_fbm_status(product)
                number_of_units = await get_number_of_units(product)
                comment = await get_comments(product)
                set_flag = await get_set_info(product)
                no_set = await get_not_set_info(product)
                number_of_sets = await get_number_of_sets(product)
                units_in_set = await number_of_units_in_set(product)

                for asin in asins:
                    amount_due = await get_amount_due(asin)
                    amount_paid = await get_amount_paid(asin)
                    order_num = await get_order_number_by_asin(asin)

                    orders_dict['Order №'].append(order_num[0])
                    orders_dict['Clients'].append(client)
                    orders_dict['Product name'].append(product)
                    orders_dict['FBA'].append('Yes' if fba else 'No')
                    orders_dict['FBM'].append('Yes' if fbm else 'No')
                    orders_dict['ASIN'].append(asin)
                    orders_dict['Number of units'].append(number_of_units)
                    orders_dict['Comment'].append(comment if comment else 'None')
                    orders_dict['Set'].append('Yes' if set_flag else 'No')
                    orders_dict['No set'].append('Yes' if no_set else 'No')
                    orders_dict['Number of sets'].append(number_of_sets if number_of_sets else 0)
                    orders_dict['Units in set'].append(units_in_set if units_in_set else 0)
                    orders_dict['Amount due'].append(amount_due)
                    orders_dict['Amount paid'].append(amount_paid)
                    orders_dict['Registration date'].append(registration_date.strftime('%d-%m-%Y'))

        df = pd.DataFrame(orders_dict)
        print(df)
        df.drop_duplicates(subset=['ASIN', 'Product name'], inplace=True)
        df.sort_values(by='Order №', inplace=True)
        logger.info("Dataframe created successfully.")

        # Создание и сохранение изображения
        file_path = f'images_reports/{client}_statistics.png'
        await create_statistics_image(df, file_path)

        # Отправка сообщения
        await bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(file_path),
                                reply_markup=set_back_to_menu(callback.from_user.language_code))
        await pls_wait_message.delete()

        logger.info("Statistics sent successfully.")

    except Exception as e:
        logger.error(f'Error in process_statistics_by_client_tg: {e}')
        await callback.answer("An error occurred. Please try again later.")


''' Handler for orders action '''


@router.callback_query(AdminCallbackFactory.filter(F.action == "look_for_order_not_paid"))
async def process_orders_not_paid(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_orders_not_paid_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in process_orders_not_paid: {e}')


''' Handler for back actions '''


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_statistics_not_paid'))
async def back(callback: CallbackQuery):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_statistics_paid'))
async def back(callback: CallbackQuery):
    try:
        logger.info(f"Back command from user {callback.from_user.id}")
        await callback.message.delete()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except ValueError as e:
        logger.error(f"Error while sending back message: {e}")
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_statistics_by_quantity'))
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


"""Find Client by Most Recent and Down by 5"""


@router.callback_query(AdminCallbackFactory.filter(F.action == 'look_for_client'))
async def find_client_by_most_recent(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        clients = await get_all_clients_sorted_by_recent_form()

        await callback.message.answer(LEXICON_CHOOSE_CLIENT.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_5_clients(clients, callback.from_user.language_code))

        await state.set_state(AdminStates.waiting_for_more_clients_info)

    except Exception as e:
        logger.error(f'Error in find_client_by_most_recent: {e}')


@router.callback_query(AdminCallbackFactory.filter(F.action == 'add_five_clients'))
async def add_five_clients(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()

        state_data = await state.get_data()
        current_index = state_data.get('client_index', 0)
        all_clients = await get_all_clients_sorted_by_recent_form()
        logger.debug(f"Current index: {current_index}, All clients: {all_clients}")

        next_index = current_index + 5
        next_clients = all_clients[next_index:next_index + 5]
        logger.debug(f"Next clients before update: {next_clients}")

        # Оновлення індексу перед відправленням відповіді
        await state.update_data(client_index=next_index)
        logger.debug(f"Index after update: {next_index}")

        if not next_clients:
            logger.info("No more clients to display.")
            await callback.message.answer(LEXICON_NO_CLIENTS.get(callback.from_user.language_code, 'en'),
                                          reply_markup=set_admin_menu(callback.from_user.language_code))
            logger.info("State cleared.")
            await state.clear()
            return

        await callback.message.answer(LEXICON_NEXT_5_CLIENTS.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_5_clients(next_clients, callback.from_user.language_code))
        logger.info("Displayed clients successfully.")

    except Exception as e:
        logger.error(f'Error in add_five_clients: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_previous_clients'))
async def back_to_previous_clients(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()

        state_data = await state.get_data()
        current_index = state_data.get('client_index', 0)
        all_clients = await get_all_clients_sorted_by_recent_form()
        logger.debug(f"Current index: {current_index}, All clients: {all_clients}")

        next_index = current_index - 5
        next_clients = all_clients[next_index:next_index + 5]
        logger.debug(f"Next clients before update: {next_clients}")

        # Оновлення індексу перед відправленням відповіді
        await state.update_data(client_index=next_index)
        logger.debug(f"Index after update: {next_index}")

        if not next_clients:
            logger.info("No more clients to display.")
            await callback.message.answer(LEXICON_NO_CLIENTS.get(callback.from_user.language_code, 'en'),
                                          reply_markup=set_admin_menu(callback.from_user.language_code))
            logger.info("State cleared.")
            await state.clear()
            return

        await callback.message.answer(LEXICON_NEXT_5_CLIENTS.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_5_clients(next_clients, callback.from_user.language_code))
        logger.info("Displayed clients successfully.")

    except Exception as e:
        logger.error(f'Error in back_to_previous_clients: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_admin_menu_clients'))
async def back_to_admin_menu_clients(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.clear()

        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in back_to_admin_menu_clients: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'choose_5_clients'))
async def choose_5_clients(callback: CallbackQuery, state: FSMContext, callback_data: AdminCallbackFactory):
    try:
        await callback.message.delete()

        form_info = await get_last_form_by_client(callback_data.client_id)
        logger.debug(f"Form info: {form_info}")
        debt_info = await get_debt_by_client(callback_data.client_id)
        amount_payable = await get_amount_due_by_client(callback_data.client_id)
        amount_paid = await get_amount_paid_by_client(callback_data.client_id)

        if amount_payable == amount_paid:
            await callback.message.answer(LEXICON_CLIENT_HAS_NO_DEBT.get(callback.from_user.language_code, 'en').format(
                client=callback_data.client_id), reply_markup=set_back_to_menu(callback.from_user.language_code))
        else:
            await callback.message.answer(LEXICON_CLIENT_HAS_DEBT.get(callback.from_user.language_code, 'en').format(
                client=callback_data.client_id, product=form_info,
                price=amount_payable, paid=amount_paid, debt=debt_info),
                reply_markup=set_back_to_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in choose_5_clients: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'back_to_admin_menu_2'))
async def back_to_admin_menu_2(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_admin_menu(callback.from_user.language_code))

    except Exception as e:
        logger.error(f'Error in back_to_admin_menu_2: {e}')
        await callback.answer("An error occurred. Please try again later.")

