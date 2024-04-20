from peewee import *
import datetime

from playhouse.migrate import PostgresqlMigrator, migrate

from config_data.config import load_config

db_config = load_config('./config_data/.env').db

# Подключение к базе данных
db = PostgresqlDatabase(
    db_config.database,
    host=db_config.db_host,
    user=db_config.db_user,
    password=db_config.db_password
)


class BaseModel(Model):
    class Meta:
        database = db


class TelegramUsers(BaseModel):
    id = AutoField()
    telegram_id = BigIntegerField(unique=True)
    telegram_username = CharField()
    telegram_fullname = CharField()
    telegram_lang = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'telegram_users'


class Roles(BaseModel):
    role_name = ForeignKeyField(TelegramUsers, backref='roles', on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'roles'


class Subscriptions(BaseModel):
    id = AutoField()
    subscription_name = CharField(unique=True)
    description = CharField()
    price = FloatField()
    button_label = CharField()

    class Meta:
        database = db
        db_table = 'subscriptions'


# class Discounts(BaseModel):
#     id = AutoField()
#     subscription_id = ForeignKeyField(Subscriptions, backref='discounts', on_delete='CASCADE')
#     description = CharField()
#     discount_size = FloatField()
#     image_url = CharField()
#     from_date = DateField()
#     to_date = DateField()
#
#     class Meta:
#         database = db
#         db_table = 'discounts'


class Form(BaseModel):
    id = AutoField()
    links = CharField()
    phone_number = CharField()
    location = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form'


class Clients(BaseModel):
    id = AutoField()
    telegram_id = ForeignKeyField(TelegramUsers, backref='clients', on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'clients'

def create_tables():
    with db:
        db.create_tables([TelegramUsers], safe=True)
        db.create_tables([Roles], safe=True)
        db.create_tables([Subscriptions], safe=True)
        # db.create_tables([Discounts], safe=True)
        db.create_tables([Form], safe=True)
        db.create_tables([Clients], safe=True)


# def do_peewee_migration():
#     """Функция миграции"""
#     migrator = PostgresqlMigrator(db)
#     migrate(
#         # migrator.drop_column('conversations', 'level'),  #  удалить
#     )

