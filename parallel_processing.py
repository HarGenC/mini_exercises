import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import pandas as pd

DEFAULT_DATA_SIZE = 1_000_000

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

def time_logger(func):
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        func_result = func(*args, **kwargs)
        time_execution = time.perf_counter() - t
        return (time_execution, func_result)
    return wrapper


def generate_data(n:int) -> int:
    return [random.randint(1, 1000) for i in range(n)]

def process_number(number:int) -> int | None:
    result = 1
    for i in range(1, number + 1):
        result *= i
    return result

@time_logger
def sync_execution(data:list):
    for number in data:
        process_number(number)

@time_logger
def thread_pool_execution(data:list, optimal_count_workerks:int):
    with ThreadPoolExecutor(max_workers=optimal_count_workerks) as executor:
        for number in data:
            executor.submit(process_number, number)

@time_logger
def multiprocessing_execution(data:list, optimal_count_workerks:int):
    with multiprocessing.Pool(processes=optimal_count_workerks) as pool:
        pool.map(process_number, data)

def worker_work_func(queue:multiprocessing.Queue, func):
    while True:
        item = queue.get(timeout=1)
        if item is None:
            break
        try:
            func(item)
        except Exception as e:
            logger.exception(f"Неожиданное исключение: {type(e).__name__} - {e}", exc_info=True)

@time_logger
def multiprocessing_with_queue_execution(data:list, optimal_count_workerks:int):
    queue = multiprocessing.Queue()
    processes = []
    for number in data:
        queue.put(number)

    for i in range(optimal_count_workerks):
        queue.put(None)

    for i in range(optimal_count_workerks):
        p = multiprocessing.Process(target=worker_work_func, args=(queue, process_number))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

def visualization_results(results):
    # Создаем DataFrame для анализа
    df = pd.DataFrame(results)
    
    # 1. Таблица результатов
    print("\n" + "="*80)
    print("ТАБЛИЦА РЕЗУЛЬТАТОВ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("="*80)
    print(df.round(3).to_string(index=False))

    df.to_csv('quick_test_results.csv', index=False)
    print("\nРезультаты сохранены в quick_test_results.csv")

if __name__ == '__main__':
    optimal_count_workerks = multiprocessing.cpu_count()
    data = generate_data(DEFAULT_DATA_SIZE)
    results = []
    results.append({"method":"sync_execution","time_execution":sync_execution(data)[0]})
    results.append({"method":"thread_pool_execution","time_execution":thread_pool_execution(data, optimal_count_workerks)[0]})
    results.append({"method":"multiprocessing_execution","time_execution":multiprocessing_execution(data, optimal_count_workerks)[0]})
    results.append({"method":"multiprocessing_with_queue_execution","time_execution":multiprocessing_with_queue_execution(data, optimal_count_workerks)[0]})
    visualization_results(results)
    