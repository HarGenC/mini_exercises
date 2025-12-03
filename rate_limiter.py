import random
import time
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class RateLimitExceed(Exception):
    pass


class RateLimiter:
    def test(self, service_name = "test") -> bool:
        self.check_and_delete_expired_time(service_name)
        if r.llen(f"limiter:{service_name}") == 5:
            return False
        return True
    
    def check_and_delete_expired_time(self, service_name):
        now = time.time()
        while True:
            expired_time_list = r.lrange(f"limiter:{service_name}", 0, 0)
            if len(expired_time_list) == 0:
                break

            expired_time = json.loads(expired_time_list[0])["expired_at"]
            if expired_time < now:
                r.lpop(f"limiter:{service_name}")
            else:
                break
    

def make_api_request(rate_limiter: RateLimiter, service_name = "test"):
    if not rate_limiter.test():
        raise RateLimitExceed
    else:
        expired_at = time.time() + 3
        r.rpush(f"limiter:{service_name}", json.dumps({"expired_at":expired_at}))


if __name__ == '__main__':
    rate_limiter = RateLimiter()

    for _ in range(50):
        time.sleep(random.randint(1, 2))

        try:
            make_api_request(rate_limiter)
        except RateLimitExceed:
            print("Rate limit exceed!")
        else:
            print("All good")