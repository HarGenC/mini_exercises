import redis
import json
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class RedisQueue:
    def publish(self, msg: dict):
            r.rpush("queue", json.dumps(msg))

    def consume(self) -> dict:
        result = json.loads(r.lpop("queue"))
        return result


if __name__ == '__main__':
    q = RedisQueue()
    q.publish({'a': 1})
    q.publish({'b': 2})
    q.publish({'c': 3})

    assert q.consume() == {'a': 1}
    assert q.consume() == {'b': 2}
    assert q.consume() == {'c': 3}