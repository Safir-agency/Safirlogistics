from config_data.config import load_config

admin_ids = load_config('./config_data/.env').tg_bot.admin_ids

def is_admin(user_id):
    """Check if a given user_id is in the list of admin IDs."""
    return user_id in admin_ids
