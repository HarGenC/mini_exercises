import logging
import json
import uvicorn
import aiohttp

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
        if response.status == 404:
            return await send_complete_response(404, json.dumps({"error": f"Unknown currency '{path}'"}), send)
    except Exception as e:
        logging.exception(e)
        return await send_complete_response(520, json.dumps({"error": "Server error"}), send)
    
    try:
        json_data = await response.json()
    except aiohttp.ContentTypeError as e:
        logging.exception(e)
        return await send_complete_response(400, json.dumps({"error": "Invalid JSON response"}), send)
    except Exception as e:
        logging.exception(e)
        return await send_complete_response(520, json.dumps({"error": "Server error"}), send)

    return await send_complete_response(200, json.dumps(json_data), send)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)