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


class TechSupport(BaseModel):
    id = AutoField()
    telegram_id = ForeignKeyField(TelegramUsers, backref='tech_support', on_delete='CASCADE')
    message = CharField(null=True)
    file_type = CharField(null=True)
    file_id = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'tech_support'

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
    order_number = CharField()
    product_name = CharField()
    FBA = BooleanField(default=False)
    FBM = BooleanField(default=False)
    ASIN = CharField()
    number_of_units = IntegerField()
    comment = CharField(null=True)
    SET = BooleanField(default=False)
    NOT_SET = BooleanField(default=False)
    number_of_units_in_set = IntegerField(null=True)
    number_of_sets = IntegerField(null=True)
    phone_number = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form'

class FormFBA(BaseModel):
    id = AutoField()
    form_id = ForeignKeyField(Form, backref='form_fba', on_delete='CASCADE')
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form_fba'


class FormFBM(BaseModel):
    id = AutoField()
    form_id = ForeignKeyField(Form, backref='form_fbm', on_delete='CASCADE')
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'form_fbm'

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

class Payment(BaseModel):
    id = AutoField()
    client_id = ForeignKeyField(Clients, backref='payments', on_delete='CASCADE')
    form_id = ForeignKeyField(Form, backref='payments', on_delete='CASCADE')
    amount_due = DecimalField(decimal_places=2)  # Загальна сума до оплати
    amount_paid = DecimalField(decimal_places=2, default=0.0)  # Сума, яка була сплачена
    is_paid = BooleanField(default=False)  # Чи була сума повністю сплачена
    due_date = DateTimeField()  # Термін оплати
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'payments'

class Invoices(BaseModel):
    id = AutoField()
    user_id = ForeignKeyField(Clients, backref='invoices', on_delete='CASCADE')
    invoice_id = CharField()
    amount = FloatField()
    payment_method = CharField()
    status = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        db_table = 'invoices'


def create_tables():
    with db:
        db.create_tables([TelegramUsers], safe=True)
        db.create_tables([Roles], safe=True)
        db.create_tables([Subscriptions], safe=True)
        db.create_tables([Form], safe=True)
        db.create_tables([FormFBA], safe=True)
        db.create_tables([FormFBM], safe=True)
        db.create_tables([SecondStage], safe=True)
        db.create_tables([SecondStageAdmin], safe=True)
        # db.create_tables([Discounts], safe=True)
        db.create_tables([Form], safe=True)
        db.create_tables([Clients], safe=True)
        db.create_tables([TechSupport], safe=True)
        db.create_tables([Payment], safe=True)
        db.create_tables([Invoices], safe=True)


def do_peewee_migration():
    """Функция миграции"""
    migrator = PostgresqlMigrator(db)
    migrate(
        migrator.add_column('form', 'order_number', CharField(null=True))
    )

