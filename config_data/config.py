from dataclasses import dataclass
from environs import Env
import peewee

@dataclass
class DatabaseConfig:
    database_url: str  # Полная URL строка для базы данных


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота
    chat_id: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('API_TOKEN'),
            admin_ids=list(map(int, env.list('ADMIN_IDS'))),
            chat_id=env('CHAT_ID')
        ),
        db=DatabaseConfig(
            database_url=env('DB_URL')
        )
    )


# Выводим значения полей экземпляра класса Config на печать,
# чтобы убедиться, что все данные, получаемые из переменных окружения, доступны
# print('API_TOKEN:', load_config('.env').tg_bot.token)
# print('ADMIN_IDS:', load_config('.env').tg_bot.admin_ids)
# print('CHAT_ID:', load_config('.env').tg_bot.chat_id)
# print('DATABASE:', load_config('.env').db.database)
# print('DB_HOST:', load_config('.env').db.db_host)
# print('DB_USER:', load_config('.env').db.db_user)
# print('DB_PASSWORD:', load_config('.env').db.db_password)
