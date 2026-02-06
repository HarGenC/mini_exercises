import logging
import json
import uvicorn
import aiohttp

class HTTPStatus:
    """Класс для хранения HTTP статус-кодов"""
    OK_200 = 200
    CREATED_201 = 201
    ACCEPTED_202 = 202
    NO_CONTENT_204 = 204
    
    BAD_REQUEST_400 = 400
    UNAUTHORIZED_401 = 401
    FORBIDDEN_403 = 403
    NOT_FOUND_404 = 404
    METHOD_NOT_ALLOWED_405 = 405
    CONFLICT_409 = 409
    UNPROCESSABLE_ENTITY_422 = 422
    TOO_MANY_REQUESTS_429 = 429
    
    INTERNAL_SERVER_ERROR_500 = 500
    BAD_GATEWAY_502 = 502
    SERVICE_UNAVAILABLE_503 = 503
    GATEWAY_TIMEOUT_504 = 504
    
    SERVER_ERROR_520 = 520
    INVALID_RESPONSE_521 = 521


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
session = None

async def send_complete_response(status:int, body:str, send):
    await send({'type': 'http.response.start',
               'status': status,
               'headers': [[b'content-type', b'application/json']]
               })
    await send({
            'type': 'http.response.body',
            "body": body.encode()})

async def lifespan(receive, send):
    global session

    event = await receive()

    if event["type"] == "lifespan.startup":
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
        await send({"type": "lifespan.startup.complete"})

    event = await receive()

    if event["type"] == "lifespan.shutdown":
        await session.close()
        await send({"type": "lifespan.shutdown.complete"})
        return

async def app(scope, receive, send):
    
    if scope["type"] == "lifespan":
        await lifespan(receive, send)
        return
    if scope['type'] != 'http':
        return
    
    path = scope["path"].lstrip("/")
    url = f"https://api.exchangerate-api.com/v4/latest/{path}"

    try:
        response = await session.get(url)
        if response.status == HTTPStatus.NOT_FOUND_404:
            return await send_complete_response(HTTPStatus.NOT_FOUND_404, json.dumps({"error": f"Unknown currency '{path}'"}), send)
    except Exception as e:
        logging.exception(e)
        return await send_complete_response(HTTPStatus.SERVER_ERROR_520, json.dumps({"error": "Server error"}), send)
    
    try:
        json_data = await response.json()
    except aiohttp.ContentTypeError as e:
        logging.exception(e)
        return await send_complete_response(HTTPStatus.BAD_REQUEST_400, json.dumps({"error": "Invalid JSON response"}), send)
    except Exception as e:
        logging.exception(e)
        return await send_complete_response(HTTPStatus.SERVER_ERROR_520, json.dumps({"error": "Server error"}), send)

    return await send_complete_response(HTTPStatus.OK_200, json.dumps(json_data), send)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)