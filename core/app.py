from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def post_message(request: Request) -> JSONResponse:
    """
    Минимальный endpoint ядра для приёма сообщений от клиентов.

    Agent Core/LLM в дальнейшем заменит эту заглушку на вызов настоящего агента.
    """
    payload = await request.json()
    user_id = str(payload.get("user_id") or "unknown")
    channel = str(payload.get("channel") or "unknown")
    text = payload.get("text") or "Пустое сообщение."

    reply_text = f"Эхо от ядра (канал={channel}, user_id={user_id}): {text}"
    return JSONResponse({"text": reply_text})


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/v1/messages", post_message, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)


