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

async def producer(urls_queue:asyncio.Queue, file_path:str, count_consumers:int) -> None:
    async with aiofiles.open(file_path, mode="r") as f:
        while True:
            url = await f.readline()
            if not url:
                break
            await urls_queue.put(url.replace("\n", ""))
        for _ in range(count_consumers):
            await urls_queue.put(None)


async def consumer(urls_queue:asyncio.Queue, content_queue:asyncio.Queue, loop:asyncio.AbstractEventLoop) -> None:
    timeout = 2
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        while True:
            url = await urls_queue.get()
            if url is None:
                urls_queue.task_done()
                break
            content = await get_content(url, session, loop)
            if content:
                await content_queue.put(content)
            urls_queue.task_done()

def should_retry(status_code: int, exception: Exception) -> bool:
    if exception:
        if isinstance(exception, (aiohttp.ClientConnectorError, asyncio.TimeoutError)):
            return True
    
    if not status_code:
        return False
    
    if status_code == 429 or (500 <= status_code <= 599):
        return True
    if 400 <= status_code < 500:
        return False
    return False


async def get_content(url:str,
                          session:aiohttp.ClientSession,
                          loop:asyncio.AbstractEventLoop) -> dict | None:
    content = None
    last_exception = None
    status_code = 0
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                if "application/json" in response.headers.get("Content-Type", ""):
                    try:
                        text = await response.text()
                        content = await loop.run_in_executor(
                        None,
                        json.loads,
                        text
                        )
                    except aiohttp.ContentTypeError as e:
                        logger.exception(f"Неверный json {type(e).__name__} - {e}")
                    except json.JSONDecodeError as e:
                        logger.exception(f"Ошибка парсинга JSON: {type(e).__name__} - {e}")
                        content = None
                break
            
        except aiohttp.ClientResponseError as e:
            last_exception = e
            if not should_retry(status_code, e):
                logger.exception(f"Ошибка HTTP: {type(e).__name__} - {e.status}", extra={"url": url, "attempt": attempt}, exc_info=True)
                break

        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
            last_exception = e

        except aiohttp.InvalidURL as e:
            logger.exception(f"Неправильный URL: {type(e).__name__} - {e}", extra={"url": url, "attempt": attempt}, exc_info=True)
            break

        except aiohttp.ClientError as e:
            logger.exception(f"Общая ошибка клиента: {type(e).__name__} - {e}", extra={"url": url, "attempt": attempt}, exc_info=True)
            break

        except Exception as e:
            logger.exception(f"Неожиданное исключение: {type(e).__name__} - {e}", extra={"url": url, "attempt": attempt}, exc_info=True)
            break

        if attempt < max_retries and should_retry(status_code, last_exception):
            delay = 2 ** (attempt - 1)
            await asyncio.sleep(delay)
        else:
            logger.exception(last_exception, extra={"url": url, "attempt": attempt}, exc_info=True)

    if content is not None:
        result_dict = {"url": url, "content": content}
        return await loop.run_in_executor(
            None,
            lambda: json.dumps(result_dict, ensure_ascii=False)
        )
                
async def write_file(queue:asyncio.Queue, file_path:str):
    async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
        while True:
            item = await queue.get()
            if item is None:
                break
            await f.write(item + "\n")
            queue.task_done()


async def fetch_urls(read_file_path:str, count_consumers:int, write_file_path:str):
    loop = asyncio.get_event_loop()
    content_queue = asyncio.Queue()
    urls_queue = asyncio.Queue()

    write_task = asyncio.create_task(write_file(content_queue, write_file_path))

    producer_task = asyncio.create_task(producer(urls_queue=urls_queue, file_path=read_file_path, count_consumers=count_consumers))
    consumers_tasks = [asyncio.create_task(consumer(urls_queue=urls_queue,
                                                    content_queue=content_queue, loop=loop)) for _ in range(count_consumers)]

    await producer_task
    await asyncio.gather(*consumers_tasks)
    await content_queue.put(None)
    await write_task


if __name__ == '__main__':
    asyncio.run(fetch_urls('./urls.txt', 10, './results.jsonl'))