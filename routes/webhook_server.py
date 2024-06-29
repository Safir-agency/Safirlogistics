# webhook_server.py
from aiohttp import web
from py_logger import get_logger

log = get_logger(__name__)

async def options_handler(request):
    """Обробник для OPTIONS запитів для підтримки CORS."""
    return web.Response(headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET',
        'Access-Control-Allow-Headers': 'Content-Type',
    })

async def webhook_handler(request):
    if request.method == 'GET':
        try:
            data = await request.json()
            log.info(f"Data received: {data}")
            product_name = data['product_name']
            asin = data['ASIN']
            phone_number = data['phone_number']
            log.info(f"ASIN: {asin}")
            log.info(f"Phone number: {phone_number}")
            log.info(f"Product name: {product_name}")
            return web.Response(text='Data received', status=200)
        except Exception as e:
            log.error(f"Error: {e}")
            return web.Response(text=str(e), status=500)
    else:
        log.error(f"Method not allowed")
        return web.Response(text='Method not allowed', status=405)


async def get_webhook_handler(request):
    """Обробник для GET запитів."""
    return web.Response(text='Webhook server is running', status=200)

async def root_handler(request):
    """Обробник для кореневого шляху."""
    return web.Response(text='Webhook server is running', status=200)


def setup_routes(app):
    app.router.add_route("POST", "/webhook", webhook_handler)
    app.router.add_route("OPTIONS", "/webhook", options_handler)
    app.router.add_route("GET", "/webhook", get_webhook_handler)
    app.router.add_route("GET", "/", root_handler)
    app.router.add_route("GET", "/submit-form", webhook_handler)