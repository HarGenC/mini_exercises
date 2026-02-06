import datetime
import time
from functools import wraps
import uuid
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)

def single(max_processing_time: datetime.timedelta):
    def decorator(func):
        lock_key = f"single:{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            token = str(uuid.uuid4())

            acquired = redis_client.set(
                lock_key,
                token,
                nx=True,
                ex=int(max_processing_time.total_seconds())  # TTL
            )

            if not acquired:
                raise RuntimeError(
                    f"Function {func.__name__} is already running somewhere else."
                )

            try:
                return func(*args, **kwargs)

            finally:
                stored_token = redis_client.get(lock_key)
                if stored_token and stored_token.decode() == token:
                    redis_client.delete(lock_key) # 

        return wrapper

    return decorator
    


@single(max_processing_time=datetime.timedelta(minutes=2))
def process_transaction():
    time.sleep(2)

process_transaction()