import asyncio
import json
import logging
import aiohttp
import aiofiles

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

urls = [
    "https://example.com",
    "https://remanga.org/manga/noblesse/vol3/160", #404 ошибка
    "https://httpbin.org/status/404", #404 только с ВПН
    "https://nonexistent.url"
]

async def get_status_code(queue:asyncio.Queue,
                          sem:asyncio.Semaphore,
                          url:str,
                          session:aiohttp.ClientSession):
    status_code = 0
    async with sem:
        try:
            async with session.get(url) as response:
                status_code = response.status
        except aiohttp.ClientConnectorError as e:
            logger.exception(f"Ошибка подключения: {type(e).__name__} - {e}")
        except asyncio.TimeoutError as e:
            logger.exception(f"Таймаут: {type(e).__name__} - {e}")
        except aiohttp.ClientResponseError as e:
            logger.exception(f"Ошибка HTTP: {type(e).__name__} - {e.status}")
        except aiohttp.InvalidURL as e:
            logger.exception(f"Неправильный URL: {type(e).__name__} - {e}")
        except aiohttp.ClientError as e:
            logger.exception(f"Общая ошибка клиента: {type(e).__name__} - {e}")
        except Exception as e:
            logger.exception(f"Неожиданное исключение: {type(e).__name__} - {e}")
            
        await queue.put(json.dumps({"url":url, "status_code":status_code}))
                
async def write_file(queue: asyncio.Queue, file_path:str):
    async with aiofiles.open(file_path, mode="w") as f:
        while True:
            item = await queue.get()
            if item is None:
                break
            await f.write(item + "\n")
            queue.task_done()


async def fetch_urls(urls: list[str], file_path: str):
    sem = asyncio.Semaphore(5)
    queue = asyncio.Queue()

    write_task = asyncio.create_task(write_file(queue, file_path))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        tasks = [asyncio.create_task(get_status_code(queue, sem, url, session)) for url in urls]
        await asyncio.gather(*tasks)

    await queue.put(None)
    await write_task


if __name__ == '__main__':
    asyncio.run(fetch_urls(urls, './results.jsonl'))