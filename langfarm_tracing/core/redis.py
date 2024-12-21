import logging
from typing import Generator

import redis

from langfarm_tracing.core.config import settings

logger = logging.getLogger(__name__)

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


def get_redis_client() -> Generator[redis.Redis, None, None]:
    r = redis.Redis(connection_pool=pool)
    logger.debug("redis client=[%s] created", redis_url)
    try:
        yield r
    finally:
        r.close()
        logger.debug("redis client=[%s] closed", redis_url)


def with_redis_client(func):

    def execute(key: str, created_at: str, *, expire_seconds: int = settings.REDIS_BODY_ID_EXPIRE_SECONDS) -> str:
        for redis_client in get_redis_client():
            return func(key, created_at, expire_seconds=expire_seconds, redis_client=redis_client)

    return execute


@with_redis_client
def read_created_at_or_set(
        key: str, created_at: str
        , *, expire_seconds: int = settings.REDIS_BODY_ID_EXPIRE_SECONDS, redis_client: redis.Redis = None
) -> str:
    # https://redis.io/docs/latest/commands/set/
    old_created_at = redis_client.set(key, created_at, ex=expire_seconds, nx=True, get=True)
    if old_created_at:
        return old_created_at.decode('utf-8')
    else:
        return created_at
