import requests
import phonenumbers
from phonenumbers import NumberParseException, carrier
from phonenumbers.phonenumberutil import number_type
from py_logger import get_logger
# from fastapi import FastAPI, Request

logger = get_logger(__name__)
# app = FastAPI()
#
#
# @app.get("/")
# async def read_root(request: Request):
#     # Get user ip, city and country provided by Cloudflare
#     user_ip = request.headers.get('CF-Connecting-IP')
#     print('user_ip', user_ip)
#     city = request.headers.get('CF-IPCity')
#     print('city', city)
#     country = request.headers.get('CF-IPCountry')
#     print('country', country)


async def fetch_user_ip(user_id):
    try:
        return requests.get('https://api.ipify.org').text
    except requests.RequestException as e:
        logger.error(f"Error fetching user ip: {e}")
        return 'Unknown'


async def fetch_user_location(user_ip):
    try:
        if user_ip != 'Unknown':
            return requests.get(f'http://ip-api.com/json/{user_ip}').json()
        else:
            return {}
    except requests.RequestException as e:
        logger.error(f"Error fetching user location: {e}")
        return {}


def custom_validate_phone(number):
    """Функція переірки валідності phone"""
    try:
        if carrier._is_mobile(number_type(phonenumbers.parse(number, None))):
            return True
        else:
            return False
    except NumberParseException as e:
        logger.error(f"ERROR: {e}  Number is not valid")
        return False