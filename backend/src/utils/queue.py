from redis import Redis
from redis.exceptions import RedisError

from src.config.settings import REDIS_URL

WAKE_KEY = 'umbrella:run-wake'
redis = Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=4)


def wake_worker():
    try:
        redis.lpush(WAKE_KEY, 'run')
    except RedisError:
        # The next SQL poll still receives the durable job.
        pass
