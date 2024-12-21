import logging
import time
import unittest

import redis

from tests.base import BaseTestCase
from langfarm_tracing.core.redis import read_created_at_or_set, pool

logger = logging.getLogger(__name__)


class MyTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.redis_client = redis.Redis(connection_pool=pool)

    def tearDown(self):
        if self.redis_client:
            self.redis_client.close()

    def redis_get_value(self, key: str) -> str | None:
        value = self.redis_client.get(key)
        if value:
            return value.decode('utf-8')
        else:
            return None

    def test_get_body_id_in_redis(self):
        topic = 'traces'
        trace_id = '35d534a3-e8b6-41e0-9554-e835d41b15a9'
        key = f"{topic}-{trace_id}"
        created_at = '2024-12-04T16:47:01.292087Z'
        expire_seconds = 10
        cache_value = read_created_at_or_set(key, created_at, expire_seconds=expire_seconds)
        assert cache_value
        # print(f"cache_value={cache_value}")
        assert cache_value == created_at

        for it in range(expire_seconds-1):
            value = self.redis_get_value(key)
            logger.info("idx=%s, get redis [v=%s, origin=%s] wait 1s ...", it, value, created_at)
            assert value
            assert value == created_at
            time.sleep(1)

        # 再等 2 秒
        logger.info("再等 2 秒 ...")
        time.sleep(2)
        value = self.redis_get_value(key)
        logger.info("get redis [v=%s, origin=%s]", value, created_at)
        assert value is None


if __name__ == '__main__':
    unittest.main()
