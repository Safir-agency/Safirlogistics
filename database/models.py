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
    product_name = CharField()
    FBA = BooleanField(default=False)
    FBM = BooleanField(default=False)
    ASIN = CharField()
    phone_number = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form'

class FormFBA(BaseModel):
    id = AutoField()
    form_id = ForeignKeyField(Form, backref='form_fba', on_delete='CASCADE')
    number_of_units = IntegerField()
    comment = CharField(default='')
    SET = BooleanField(default=False)
    NOT_SET = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form_fba'


class FormFBM(BaseModel):
    id = AutoField()
    form_id = ForeignKeyField(Form, backref='form_fbm', on_delete='CASCADE')
    number_of_units = IntegerField()
    SET = BooleanField(default=False)
    NOT_SET = BooleanField(default=False)
    comment = CharField(default='')
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form_fbm'


class Set(BaseModel):
    id = AutoField()
    form_fba_id = ForeignKeyField(FormFBA, backref='set', on_delete='CASCADE')
    form_fbm_id = ForeignKeyField(FormFBM, backref='set', on_delete='CASCADE')
    number_of_units_in_set = IntegerField()
    number_of_sets = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'set'

class SecondStage(BaseModel):
    id = AutoField()
    form_fba_id = ForeignKeyField(FormFBA, backref='second_stage', on_delete='CASCADE')
    FNSKU_label = CharField()
    shipping_label = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'second_stage'

class SecondStageAdmin(BaseModel):
    id = AutoField()
    form_fba_id = ForeignKeyField(FormFBA, backref='second_stage', on_delete='CASCADE')
    weight = FloatField()
    dimensions = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'second_stage_admin'

class Clients(BaseModel):
    id = AutoField()
    telegram_id = ForeignKeyField(TelegramUsers, backref='clients', on_delete='CASCADE')
    form_id = ForeignKeyField(Form, backref='clients', on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'clients'

def create_tables():
    with db:
        db.create_tables([TelegramUsers], safe=True)
        db.create_tables([Roles], safe=True)
        db.create_tables([Subscriptions], safe=True)
        db.create_tables([Form], safe=True)
        db.create_tables([FormFBA], safe=True)
        db.create_tables([FormFBM], safe=True)
        db.create_tables([Set], safe=True)
        db.create_tables([SecondStage], safe=True)
        db.create_tables([SecondStageAdmin], safe=True)
        # db.create_tables([Discounts], safe=True)
        db.create_tables([Form], safe=True)
        db.create_tables([Clients], safe=True)


# def do_peewee_migration():
#     """Функция миграции"""
#     migrator = PostgresqlMigrator(db)
#     migrate(
#         # migrator.drop_column('conversations', 'level'),  #  удалить
#     )

