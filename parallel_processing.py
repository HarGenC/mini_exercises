import random
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import pandas as pd

def time_logger(func):
    def wrapper(*args, **kwargs):
        t = time.time()
        func_result = func(*args, **kwargs)
        time_execution = time.time() - t
        return (time_execution, func_result)
    return wrapper


def generate_data(n:int) -> int:
    return [random.randint(1, 1000) for i in range(n)]

def process_number(number:int) -> int:
    result = 1
    for i in range(1, number + 1):
        result *= i
    return result

@time_logger
def sync_execution(data:list):
    for number in data:
        process_number(number)

@time_logger
def thread_pool_execution(data:list):
    with ThreadPoolExecutor(max_workers=100) as executor:
        for number in data:
            executor.submit(process_number, number)

@time_logger
def multiprocessing_execution(data:list):
    with multiprocessing.Pool(processes=12) as pool:
        pool.map(process_number, data)

def worker_work_func(queue:multiprocessing.Queue, func):
    while True:
        item = queue.get()
        if item is None:
            break
        func(item)

@time_logger
def multiprocessing_with_queue_execution(data:list):
    queue = multiprocessing.Queue()
    processes = []
    for number in data:
        queue.put(number)

    for i in range(12):
        queue.put(None)

    for i in range(12):
        p = multiprocessing.Process(target=worker_work_func, args=(queue, process_number))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

def vizualization_results(results):
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
    data = generate_data(1_000_000)
    results = []
    results.append({"method":"sync_execution","time_execution":sync_execution(data)[0]})
    results.append({"method":"thread_pool_execution","time_execution":thread_pool_execution(data)[0]})
    results.append({"method":"multiprocessing_execution","time_execution":multiprocessing_execution(data)[0]})
    results.append({"method":"multiprocessing_with_queue_execution","time_execution":multiprocessing_with_queue_execution(data)[0]})
    vizualization_results(results)
    