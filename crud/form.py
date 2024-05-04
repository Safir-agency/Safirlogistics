from database.models import Form
from py_logger import get_logger

logger = get_logger(__name__)


form_data = {
    "test_user": {
        # "telegram_id": 123456789,
        "form": {
            "product_name": "Test product",
            "ASIN": ["B08Y5V8JLH"],
            "phone_number": "+380123456789",
            "FBA": True, # or False,
            "FBM": False, # or True
            "FBA_details": {
                "number_of_units": 1234,
                "SET": True, # or False,
                "NOT_SET": False, # or True,
                "SET_details": {
                    "number_of_units_in_set": 100,
                    "number_of_sets": 12
                },
                "comment": "Test comment"
            },
            "FBM_details": {
                "number_of_units": 1234,
                "SET": False, # or True,
                "NOT_SET": True, # or False,
                "comment": "Optional comment for FBM"
            }
        }
    }
}

# def save_form_to_db(form_data):
#     try:
#         form, created = Form.get_or_create(
#             product_name=form_data["product_name"],
#             ASIN=form_data["ASIN"],
#             phone_number=form_data["phone_number"],
#             FBA=form_data["FBA"],
#             FBM=form_data["FBM"]
#         )
#
#         if created:
#             logger.info(f"New application saved to database: {form.product_name}")
#             if form_data["FBA"]:
#                 save_fba_form(form, form_data["FBA_details"])
#             elif form_data["FBM"]:
#                 save_fbm_form(form, form_data["FBM_details"])
#
#         logger.info(f"New application saved to database: {form.product_name}")
#         return form.id
#     except DoesNotExist as e:
#         logger.error(f"Error while saving application to database: {e}")
#         return None
