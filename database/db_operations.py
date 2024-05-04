import asyncio
import re
from peewee import DoesNotExist
from typing import Tuple, List

from database.models import TelegramUsers, Subscriptions, Form, Clients
from py_logger import get_logger
from datetime import datetime, time

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
