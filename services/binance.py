from binance.client import Client
import os
from config_data.config import Config, load_config

config: Config = load_config('./config_data/.env')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_SECRET_KEY')


if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise ValueError("Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
else:
    print("Binance API keys are set.")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)


def create_usdt_address():
    address_info = client.get_deposit_address(coin='USDT')
    return address_info['address']


usdt_address = create_usdt_address()
print(f"USDT Address: {usdt_address}")


def check_payment_status(address, amount):
    # Получаем историю депозитов
    deposits = client.get_deposit_history(asset='USDT')

    for deposit in deposits:
        if deposit['address'] == address and float(deposit['amount']) >= amount and deposit['status'] == 1:
            return True  # Платеж получен

    return False  # Платеж не получен

#
# # Пример использования
# address = usdt_address
# amount = 10.0
#
# if check_payment_status(address, amount):
#     print("Payment received!")
# else:
#     print("Payment not yet received.")
