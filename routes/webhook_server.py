# webhook_server.py
from aiohttp import web

async def options_handler(request):
    """Обробник для OPTIONS запитів для підтримки CORS."""
    return web.Response(headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET',
        'Access-Control-Allow-Headers': 'Content-Type',
    })

async def webhook_handler(request):
    """Обробник веб-хуків, який приймає тільки POST запити."""
    if request.method == 'POST':
        data = await request.json()
        print("Received data:", data)
        return web.Response(text='Webhook received', status=200)
    else:
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
