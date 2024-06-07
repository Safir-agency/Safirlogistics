import asyncio
import re
from peewee import DoesNotExist, fn
from typing import Tuple, List
from dateutil.relativedelta import relativedelta

from database.models import TelegramUsers, Subscriptions, Form, Clients, TechSupport, Payment
from py_logger import get_logger
from datetime import datetime, time, timedelta

logger = get_logger(__name__)


# Save user to db if not exists
async def save_user_to_db(user_data):
    try:
        user, created = TelegramUsers.get_or_create(
            telegram_id=user_data.telegram_id,
            defaults={
                'telegram_username': user_data.telegram_username,
                'telegram_fullname': user_data.telegram_fullname,
                'telegram_lang': user_data.telegram_lang
            }
        )

        if created:
            print(f"New user saved to database: {user.telegram_username}")
        else:
            print(f"User already exists in database: {user.telegram_username}")

    except Exception as e:
        print(f"Error while saving user to database: {e}")


async def save_user_tech_support(telegram_id, message, file_type, file_id):
    try:
        user = TelegramUsers.get(TelegramUsers.telegram_id == telegram_id)
        client, created = TechSupport.get_or_create(
            telegram_id=user.id,
            message=message,
            file_type=file_type,
            file_id=file_id)

        if created:
            logger.info(f"New client saved to database tech support: {client.telegram_id}")
        else:
            logger.info(f"Cannot create client: {client.telegram_id}")

    except Exception as e:
        print(f"Error while saving client to database tech support: {e}")


async def get_telegram_user_id(username):
    try:
        user = TelegramUsers.get(TelegramUsers.telegram_id == username)
        return user.id
    except TelegramUsers.DoesNotExist:
        print(f"User with username {username} not found.")
        return None


async def save_subscription(subscription_name, description, price, button_label):
    try:
        subscription, created = Subscriptions.get_or_create(
            subscription_name=subscription_name,
            description=description,
            price=price,
            button_label=button_label)

        if created:
            logger.info(f"New subscription saved to database: {subscription.subscription_name}")

    except ValueError as e:
        logger.error(f"Error while saving subscription to database: {e}")


async def subscription_list():
    try:
        subscriptions = Subscriptions.select()
        return subscriptions
    except ValueError as e:
        logger.error(f"Error while getting subscriptions from database: {e}")


async def get_subscription_by_id(subscription_id: int) -> Subscriptions or None:
    try:
        subscription = Subscriptions.get(Subscriptions.id == subscription_id)
        return subscription
    except Subscriptions.DoesNotExist:
        logger.error(f"Subscription with name {subscription_id} not found.")
        return None


async def delete_subscription(subscription_id: int):
    try:
        subscription = Subscriptions.get(Subscriptions.id == subscription_id)
        subscription.delete_instance()
        logger.info(f"Subscription Id: {subscription_id} - {subscription.subscription_name} deleted from database")
    except Subscriptions.DoesNotExist:
        logger.error(f"Subscription with name {subscription_id} not found.")


async def save_product_name(product_name):
    try:
        product, created = Form.get_or_create(
            product_name=product_name)

        if created:
            logger.info(f"New product saved to database: {product.product_name}")
        else:
            logger.info(f"Product does not created: {product.product_name}")

    except ValueError as e:
        logger.error(f"Error while saving product to database: {e}")


async def change_fba_status(product_name, status):
    try:
        logger.info(f"Product name: {product_name}, status FBA: {status}")
    except ValueError as e:
        logger.error(f"Error while changing FBA status: {e}")


async def change_fbm_status(product_name, status):
    try:
        logger.info(f"Product name: {product_name}, status FBM: {status}")
    except ValueError as e:
        logger.error(f"Error while changing FBM status: {e}")


async def save_application_to_db(product_name, asin, phone_number, choice):
    try:
        form, created = Form.get_or_create(
            product_name=product_name,
            ASIN=asin,
            phone_number=phone_number)

        if created:
            logger.info(f"New application saved to database: {form.product_name}")
            if choice == 'FBA':
                await change_fba_status(product_name, True)
                await change_fbm_status(product_name, False)
            elif choice == 'FBM':
                await change_fba_status(product_name, False)
                await change_fbm_status(product_name, True)

        logger.info(f"New application saved to database: {form.product_name}")
        return form.id
    except DoesNotExist as e:
        logger.error(f"Error while saving application to database: {e}")
        return None


async def save_client_to_db(telegram_id, form_id):
    try:
        client, created = Clients.get_or_create(
            telegram_id=TelegramUsers.get(TelegramUsers.telegram_id == telegram_id).id,
            form_id=form_id)

        logger.info(f"telegram_id: {telegram_id} with form_id: {form_id}")

        if created:
            logger.info(f"New client saved to database: {client.telegram_id}")
        else:
            logger.info(f"Cannot create client: {client.telegram_id}")

    except Exception as e:
        logger.error(f"Error while saving client to database: {e}")


""" Admin panel """

""" Statistics """


async def get_order_number_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Form.select(Form.order_number)
                     .join(Clients, on=(Clients.form_id == Form.id))
                     .where(Clients.telegram_id == user_id))
            order_numbers = [order.order_number for order in query]

            # logger.info(f"All order numbers by client {telegram_username}: {order_numbers}")
            return order_numbers
        # else:
        #     logger.error(f"No user found with username: {telegram_username}")
        #     return []
    except Exception as e:
        logger.error(f"Error while getting all order numbers by client from database: {e}")
        return []


async def get_clients_telegram_username():
    try:
        # Get all clients from database and their Telegram usernames
        clients = Clients.select(Clients.telegram_id, TelegramUsers.telegram_username).join(TelegramUsers).dicts()
        username = [client['telegram_username'] for client in clients]

        return username
    except Exception as e:
        logger.error(f"Error while getting clients from database: {e}")
        return None


async def get_first_order_date_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Form.select(Form.created_at)
                     .join(Clients, on=(Clients.form_id == Form.id))
                     .where(Clients.telegram_id == user_id)
                     .order_by(Form.created_at.asc())
                     .limit(1))
            date_time = query[0].created_at

            # logger.info(f"First order date by client {telegram_username}: {date_time}")
            return date_time
        # else:
        #     logger.error(f"No user found with username: {telegram_username}")
        #     return None
    except Exception as e:
        logger.error(f"Error while getting first order date by client from database: {e}")
        return None


async def get_quantity_of_orders_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Form.select(Form.product_name)
                     .join(Clients, on=(Clients.form_id == Form.id))
                     .where(Clients.telegram_id == user_id))
            quantity = query.count()

            # logger.info(f"Quantity of orders by client {telegram_username}: {quantity}")
            return quantity
        # else:
        #     logger.error(f"No user found with username: {telegram_username}")
        #     return None
    except Exception as e:
        logger.error(f"Error while getting quantity of orders by client from database: {e}")
        return None


async def get_product_name_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Form.select(Form.product_name)
                     .join(Clients, on=(Clients.form_id == Form.id))
                     .where(Clients.telegram_id == user_id))
            product_names = [product.product_name for product in query]

            # logger.info(f"All product names by client {telegram_username}: {product_names}")
            return product_names
        # else:
        #     logger.error(f"No user found with username: {telegram_username}")
        #     return []
    except Exception as e:
        logger.error(f"Error while getting all product names by client from database: {e}")
        return []


async def get_fba_status(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.FBA
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def get_fbm_status(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.FBM
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def get_asin(product_name):
    try:
        # Використовуємо select().where() для отримання всіх відповідних записів
        forms = Form.select().where(Form.product_name == product_name)
        asins = {form.ASIN for form in forms}  # Створюємо множину унікальних ASIN

        # if asins:
        #     logger.info(f"Product name: {product_name}, ASINs: {asins}")
        #     return asins
        # else:
        #     logger.error(f"No ASINs found for product name: {product_name}")
        #     return None
    except Exception as e:
        logger.error(f"Error while getting ASINs for product name {product_name}: {e}")
        return None


async def get_number_of_units(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.number_of_units
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def sum_units_by_client(telegram_username):
    try:
        total_units_by_client = (Form.select(fn.SUM(Form.number_of_units).alias('total_units'))
                                    .join(Clients, on=(Clients.form_id == Form.id))
                                    .join(TelegramUsers, on=(Clients.telegram_id == TelegramUsers.id))
                                    .where(TelegramUsers.telegram_username == telegram_username)
                                    .scalar())

        return total_units_by_client
    except Exception as e:
        logger.error(f"Error while getting total units by client from database: {e}")
        return 0

async def get_comments(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.comment
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def get_set_info(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.SET
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def get_not_set_info(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.NOT_SET
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


""" IF SET """


async def get_number_of_sets(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.number_of_sets
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


async def number_of_units_in_set(product_name):
    try:
        form = Form.get(Form.product_name == product_name)
        return form.number_of_units_in_set
    except Form.DoesNotExist:
        logger.error(f"Product with name {product_name} not found.")
        return None


"""Payment info"""


async def get_amount_due(order_number):
    try:
        form = Form.get(Form.order_number == order_number)
        amount_due = Payment.select(Payment.amount_due).where(Payment.form_id == form.id).scalar()
        if amount_due is None or amount_due == 0:
            logger.error(f"No amount due found for order number: {order_number}")
            return 0
        return amount_due
    except Exception as e:
        logger.error(f"Exception in get_amount_due for {order_number}: {str(e)}")
        return 0


async def get_amount_paid(order_number):
    try:
        form = Form.get(Form.order_number == order_number)
        amount_paid = Payment.select(Payment.amount_paid).where(Payment.form_id == form.id).scalar()
        if amount_paid is None:
            logger.error(f"No amount paid found for order number: {order_number}")
            return 0
        return amount_paid
    except Exception as e:
        logger.error(f"Exception in get_amount_paid for {order_number}: {str(e)}")
        return 0


"""Look for clients"""


async def get_all_clients_sorted_by_recent_form():
    try:
        # Запит для отримання 5 найновіших форм
        recent_forms = (Form.select(Form, Clients.telegram_id)
                        .join(Clients, on=(Form.id == Clients.form_id))
                        .order_by(Form.created_at.desc()))

        # Створення списку з ідентифікаторів телеграм-користувачів, які подали ці форми
        telegram_user_ids = [form.clients.telegram_id for form in recent_forms]

        # Запит до бази даних для отримання імен користувачів за їхніми ідентифікаторами
        users = TelegramUsers.select().where(TelegramUsers.id.in_(telegram_user_ids))
        usernames = [user.telegram_username for user in users]

        return usernames
    except Exception as e:
        logger.error(f"Error while getting clients from database: {e}")
        return None


async def get_last_form_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Form.select(Form.product_name)
                     .join(Clients, on=(Clients.form_id == Form.id))
                     .where(Clients.telegram_id == user_id)
                     .order_by(Form.created_at.desc())
                     .limit(1))
            product_name = query[0].product_name
            date_time = query[0].created_at

            logger.info(f"Last form by client {telegram_username}: {product_name}")
            return product_name
        else:
            logger.error(f"No user found with username: {telegram_username}")
            return None
    except Exception as e:
        logger.error(f"Error while getting last form by client from database: {e}")
        return None


async def get_debt_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Payment.select(Payment.amount_due, Payment.amount_paid)
                     .join(Clients)
                     .join(TelegramUsers)
                     .where(TelegramUsers.id == user_id)
                     .order_by(Payment.created_at.desc())
                     .limit(1))
            if query.exists():
                amount_due = query[0].amount_due
                print(f"Amount due: {amount_due}")
                amount_paid = query[0].amount_paid
                print(f"Amount paid: {amount_paid}")
                debt = amount_due - amount_paid
                logger.info(f"Debt by client {telegram_username}: {debt}")

                return debt
            else:
                logger.info(f"Client {telegram_username} has no debt.")
                return 0
        else:
            logger.error(f"No user found with username: {telegram_username}")
            return None
    except Exception as e:
        logger.error(f"Error while getting debt by client from database: {e}")
        return None


async def get_amount_due_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Payment.select(Payment.amount_due)
                     .join(Clients)
                     .join(TelegramUsers)
                     .where(TelegramUsers.id == user_id)
                     .order_by(Payment.created_at.desc())
                     .limit(1))
            if query.exists():
                amount_due = query[0].amount_due
                logger.info(f"Amount due by client {telegram_username}: {amount_due}")

                return amount_due
            else:
                logger.info(f"Client {telegram_username} has no debt.")
                return 0
        else:
            logger.error(f"No user found with username: {telegram_username}")
            return None
    except Exception as e:
        logger.error(f"Error while getting amount due by client from database: {e}")
        return None


async def get_amount_paid_by_client(telegram_username):
    try:
        user_id = TelegramUsers.select(TelegramUsers.id).where(
            TelegramUsers.telegram_username == telegram_username).scalar()

        if user_id:
            query = (Payment.select(Payment.amount_paid)
                     .join(Clients)
                     .join(TelegramUsers)
                     .where(TelegramUsers.id == user_id)
                     .order_by(Payment.created_at.desc())
                     .limit(1))
            if query.exists():
                amount_paid = query[0].amount_paid
                logger.info(f"Amount paid by client {telegram_username}: {amount_paid}")

                return amount_paid
            else:
                logger.info(f"Client {telegram_username} has no debt.")
                return 0
        else:
            logger.error(f"No user found with username: {telegram_username}")
            return None
    except Exception as e:
        logger.error(f"Error while getting amount paid by client from database: {e}")
        return None


"""Look for orders not paid"""


async def get_not_paid_orders_by_last_7_days():
    try:
        # Query the database for all unpaid orders from the last 7 days (is_paid = False)
        not_paid_orders = (Payment.select(Payment.amount_due, Payment.amount_paid, Payment.is_paid,
                                          Clients.telegram_id.alias('client_id'), Form.product_name)
                           .join(Clients)
                           .join(Form)
                           .join(TelegramUsers, on=(Clients.telegram_id == TelegramUsers.id))
                           .where(Payment.is_paid == False,
                                  Payment.created_at >= datetime.now() - timedelta(days=7))).dicts()

        for order in not_paid_orders:
            print(order)

        return not_paid_orders

    except Exception as e:
        logger.error(f"Error while getting not paid orders from database: {e}")
        return None


async def get_not_paid_orders_by_last_30_days():
    try:
        # Query the database for all unpaid orders from the last 30 days (is_paid = False)
        not_paid_orders = (Payment.select(Payment.amount_due, Payment.amount_paid, Payment.is_paid,
                                          Clients.telegram_id.alias('client_id'), Form.product_name)
                           .join(Clients)
                           .join(Form)
                           .join(TelegramUsers, on=(Clients.telegram_id == TelegramUsers.id))
                           .where(Payment.is_paid == False,
                                  Payment.created_at >= datetime.now() - timedelta(days=30))).dicts()

        for order in not_paid_orders:
            print(order)

        return not_paid_orders

    except Exception as e:
        logger.error(f"Error while getting not paid orders from database: {e}")
        return None


async def get_not_paid_orders_by_last_half_year():
    try:
        # Query the database for all unpaid orders from the last half year (is_paid = False)
        not_paid_orders = (Payment.select(Payment.amount_due, Payment.amount_paid, Payment.is_paid,
                                          Clients.telegram_id.alias('client_id'), Form.product_name)
                           .join(Clients)
                           .join(Form)
                           .join(TelegramUsers, on=(Clients.telegram_id == TelegramUsers.id))
                           .where(Payment.is_paid == False,
                                  Payment.created_at >= datetime.now() - timedelta(days=180))).dicts()

        for order in not_paid_orders:
            print(order)

        return not_paid_orders

    except Exception as e:
        logger.error(f"Error while getting not paid orders from database: {e}")
        return None


async def get_not_paid_orders_by_last_1_year():
    try:
        # Query the database for all unpaid orders from the last 1 year (is_paid = False)
        not_paid_orders = (Payment.select(Payment.amount_due, Payment.amount_paid, Payment.is_paid,
                                          Clients.telegram_id.alias('client_id'), Form.product_name)
                           .join(Clients)
                           .join(Form)
                           .join(TelegramUsers, on=(Clients.telegram_id == TelegramUsers.id))
                           .where(Payment.is_paid == False,
                                  Payment.created_at >= datetime.now() - relativedelta(years=1))).dicts()

        for order in not_paid_orders:
            print(order)

        return not_paid_orders

    except Exception as e:
        logger.error(f"Error while getting not paid orders from database: {e}")
        return None


async def get_products_not_paid():
    try:
        # Query the database for all unpaid orders from the last 7 days (is_paid = False)
        query = Form.select(Form.product_name).join(Clients).join(Payment).where(
            Payment.is_paid == False).dicts()

        product_name = list(query)
        return product_name

    except Exception as e:
        logger.error(f"Error while getting product from database: {e}")
        return None


async def get_clients_not_paid():
    try:
        # Query the database for all unpaid orders from the last 7 days (is_paid = False)
        query = TelegramUsers.select(
            TelegramUsers.telegram_username).join(Clients).join(
            Payment).where(Payment.is_paid == False).dicts()

        client_name = list(query)
        print(client_name)
        return client_name

    except Exception as e:
        logger.error(f"Error while getting client from database: {e}")
        return None
