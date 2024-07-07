import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import pytz
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import FSInputFile
import qrcode
from reportlab.lib.pagesizes import letter, A6
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from bot_init import bot
from database.db_operations import get_clients_telegram_username, \
    get_product_name_by_client, get_all_clients_sorted_by_recent_form, \
    get_last_form_by_client, \
    get_first_order_date_by_client, \
    get_quantity_of_orders_by_client, get_order_number_by_client, sum_units_by_client, get_info_by_product_name, \
    get_order_number_by_asin, get_info_by_client, get_amounts_by_asin, get_amounts_by_order_number, get_asin, \
    get_telegram_user_id, get_telegram_id_by_username
from filters.is_admin import is_admin
from keyboards.keyboard_admin import set_admin_menu, set_statistics_menu, set_choose_client, \
    set_choose_client_phone, set_choose_5_clients, set_back_to_menu, set_choose_client_for_receipt, payment_button
from lexicon.lexicon import LEXICON_RECEIPT
from lexicon.lexicon_admin import LEXICON_CHOOSE_ACTION, LEXICON_NO_ACCESS, LEXICON_CHOOSE_CLIENT, LEXICON_NO_CLIENTS, \
    LEXICON_NEXT_5_CLIENTS, LEXICON_CLIENT_HAS_NO_DEBT, LEXICON_CLIENT_HAS_DEBT, \
    LEXICON_STATISTICS_SEND_SUCCESS, LEXICON_PLEASE_WAIT, LEXICON_RECEIPT_SENT
from py_logger import get_logger
from states.states_admin import AdminCallbackFactory, AdminStates

logger = get_logger(__name__)

router = Router()
tech_support_chat_id = os.getenv('CHAT_ID')


async def create_statistics_image(df: pd.DataFrame, file_path: str):
    try:
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
            elif j == df.columns.get_loc('Amount paid') and df.iloc[i - 1]['Amount paid'] < df.iloc[i - 1][
                'Amount due']:
                cell.set_facecolor('orange')  # Оранжевый цвет для строк с amount_paid < amount_due
                cell.set_text_props(color='black')
            else:
                cell.set_facecolor(cell_colors[i % len(cell_colors)])
                cell.set_text_props(color='black')

        # Сохраняем изображение
        plt.savefig(file_path)
        plt.close()

    except ValueError as e:
        logger.error(f"Error in create_statistics_image: {e}")

def generate_receipt(client_name, service_name, order_id, amount, receipt_id, date, output_filename):
    # Преобразование списков в строки
    service_name_str = ", ".join(service_name)
    order_id_str = ", ".join(order_id)

    # Создание PDF-документа
    c = canvas.Canvas(output_filename, pagesize=A6)
    width, height = A6

    # Установка цветов и стилей
    c.setStrokeColorRGB(0.2, 0.5, 0.3)
    c.setFillColorRGB(0.2, 0.5, 0.3)
    c.rect(0, height - inch * 0.5, width, inch * 0.4, fill=1)

    # Заголовок чека
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(width / 2.0, height - inch * 0.40, "Payment Receipt")

    # ID чека и дата
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(inch * 0.5, height - inch * 1.0, f"Receipt ID: {receipt_id}")
    c.drawString(inch * 0.5, height - inch * 1.3, f"Date: {date}")

    # Информация о клиенте
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch * 0.5, height - inch * 1.8, "Client Information")
    c.setFont("Helvetica", 10)
    c.drawString(inch * 0.5, height - inch * 2.1, f"Telegram username: {client_name}")

    # Информация о услуге
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch * 0.5, height - inch * 2.6, "Service Information")
    c.setFont("Helvetica", 10)
    c.drawString(inch * 0.5, height - inch * 2.9, f"Order IDs: {order_id_str}")
    c.drawString(inch * 0.5, height - inch * 3.2, f"Product names: {service_name_str}")
    c.drawString(inch * 0.5, height - inch * 3.5, f"Amount: {amount:.2f}$")

    # Подпись
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch * 0.5, inch * 0.5, "Thank you for your payment!")

    # Сохранить PDF
    c.showPage()
    c.save()

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
                amount_paid, amount_due = await get_amounts_by_order_number(order_number)
                total_amount_due += amount_due
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
        logger.info(f"Orders number: {orders_number}")
        product_names = await get_product_name_by_client(client)
        logger.info(f"Product names: {product_names}")
        registration_date = await get_first_order_date_by_client(client)
        logger.info(f"Registration date: {registration_date}")

        for order_number in orders_number:
            logger.info(f"Order number: {order_number}")
            for product in product_names:
                logger.info(f"Product name: {product}")
                get_info_by_prod = await get_info_by_product_name(product)
                asins = await get_asin(product)
                fba = get_info_by_prod['FBA']
                fbm = get_info_by_prod['FBM']
                number_of_units = get_info_by_prod['number_of_units']
                comment = get_info_by_prod['comment']
                set_flag = get_info_by_prod['SET']
                no_set = get_info_by_prod['NOT_SET']
                number_of_sets = get_info_by_prod['number_of_sets']
                units_in_set = get_info_by_prod['number_of_units_in_set']
                logger.info(f"Get info by product: {get_info_by_prod}")

                for asin in asins:
                    logger.info(f"ASIN: {asin}")
                    amount_details = await get_amounts_by_asin(asin)
                    amount_due = amount_details[1]
                    amount_paid = amount_details[0]
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

    except ValueError as e:
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
                amount_paid, amount_due = await get_amounts_by_order_number(order_number)
                total_amount_due += amount_due
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
                get_info_by_prod = await get_info_by_product_name(product)
                asins = await get_asin(product)
                fba = get_info_by_prod['FBA']
                fbm = get_info_by_prod['FBM']
                number_of_units = get_info_by_prod['number_of_units']
                comment = get_info_by_prod['comment']
                set_flag = get_info_by_prod['SET']
                no_set = get_info_by_prod['NOT_SET']
                number_of_sets = get_info_by_prod['number_of_sets']
                units_in_set = get_info_by_prod['number_of_units_in_set']

                for asin in asins:
                    amounts = await get_amounts_by_asin(asin)
                    amount_due = float(amounts[1])
                    amount_paid = float(amounts[0])
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
        df.sort_values(by='Order №', inplace=True)
        logger.info("Dataframe created successfully.")

        # Создание и сохранение изображения
        file_path = f'images_reports/{client}_statistics.png'
        await create_statistics_image(df, file_path)
        logger.info("Image created successfully.")

        # Отправка сообщения
        await bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(file_path),
                                reply_markup=set_back_to_menu(callback.from_user.language_code))
        logger.info("Image sent successfully.")

        await pls_wait_message.delete()
        logger.info("State cleared.")

        logger.info("Statistics sent successfully.")

    except Exception as e:
        logger.error(f'Error in process_statistics_by_client_tg: {e}')
        await callback.answer("An error occurred. Please try again later.")


# @router.callback_query(AdminCallbackFactory.filter(F.action == "look_for_order_not_paid"))
# async def process_orders_not_paid(callback: CallbackQuery):
#     try:
#         await callback.message.delete()
#         await callback.message.answer(LEXICON_CHOOSE_ACTION.get(callback.from_user.language_code, 'en'),
#                                       reply_markup=set_orders_not_paid_menu(callback.from_user.language_code))
#
#     except Exception as e:
#         logger.error(f'Error in process_orders_not_paid: {e}')


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
        # debt_info = await get_debt_by_client(callback_data.client_id)
        # amount_payable = await get_amount_due_by_client(callback_data.client_id)
        info = await get_info_by_client(callback_data.client_id)
        amount_payable = info['amount_due']
        amount_paid = info['amount_paid']
        debt_info = info['debt']

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


@router.callback_query(AdminCallbackFactory.filter(F.action == 'receipt_text'))
async def receipt_text(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("receipt_text command")
        await callback.message.delete()
        clients = await get_clients_telegram_username()
        # get unique clients
        clients = list(set(clients))
        await callback.message.answer(LEXICON_CHOOSE_CLIENT.get(callback.from_user.language_code, 'en'),
                                      reply_markup=set_choose_client_for_receipt(clients))

        await state.set_state(AdminStates.waiting_for_username_client)
        logger.info("Waiting for client.")

    except Exception as e:
        logger.error(f'Error in receipt_text: {e}')
        await callback.answer("An error occurred. Please try again later.")


@router.callback_query(AdminCallbackFactory.filter(F.action == 'set_choose_client_for_receipt'))
async def choose_client_for_receipt(callback: CallbackQuery, callback_data: AdminCallbackFactory, state: FSMContext):
    try:
        await callback.message.delete()
        client_id = callback_data.client_id
        logger.info(f"You chose client: {client_id}")

        tg_user_id = await get_telegram_id_by_username(client_id)
        logger.info(f"Telegram user ID: {tg_user_id}")

        # Отримання інформації про клієнта
        client_info = await get_info_by_client(client_id)
        product_info = await get_product_name_by_client(client_id)
        products_name = product_info[0]
        logger.info(f"Product name: {products_name}")
        order_ids = product_info[1]
        logger.info(f"Order IDs: {order_ids}")
        amount_due = client_info['amount_due']
        amount_paid = client_info['amount_paid']
        debt = client_info['debt']
        receipt_id = '1234567890'
        date = datetime.now().strftime('%Y-%m-%d')

        if amount_due == amount_paid:
            await callback.message.answer(LEXICON_CLIENT_HAS_NO_DEBT.get(callback.from_user.language_code, 'en').format(
                client=client_id), reply_markup=set_back_to_menu(callback.from_user.language_code))
            return

        # Генерація PDF чека
        output_filename = f"receipts/receipt_{client_id}.pdf"
        generate_receipt(client_name=client_id, service_name=products_name, order_id=order_ids, amount=debt,
                         receipt_id=receipt_id, date=date, output_filename=output_filename)

        # Відправка PDF чека адміністратору
        await bot.send_document(chat_id=callback.from_user.id, document=FSInputFile(output_filename),
                                caption=LEXICON_RECEIPT_SENT.get(callback.from_user.language_code, 'en'),
                                reply_markup=set_back_to_menu(callback.from_user.language_code))

        # Відправка PDF чека користувачу
        await bot.send_document(chat_id=tg_user_id, document=FSInputFile(output_filename),
                                caption=LEXICON_RECEIPT.get(callback.from_user.language_code, 'en').format(
                                    products_name=products_name, debt=debt), reply_markup=payment_button(amount=debt))

        await state.clear()

    except Exception as e:
        logger.error(f'Error in choose_client_for_receipt: {e}')
        await callback.answer("An error occurred. Please try again later.")
