import unittest
import uuid

from langfarm_tracing.core.tools import rewrite_uuid, utc_time_to_ltz
from tests.base import BaseTestCase


class MyTestCase(BaseTestCase):

    def test_uuid_rewrite(self):
        v4_str = '35d534a3-e8b6-41e0-9554-e835d41b15a9'
        v4 = uuid.UUID(v4_str)
        orig_str = '2024-12-04T16:47:01.291867Z'
        new_time = utc_time_to_ltz(orig_str)
        # print('new_time', new_time)
        new_ts = new_time.timestamp()
        # 100 纳秒 也是 0.1 微秒
        nanoseconds_100 = int(new_ts * 1000000) * 10
        # UUID epoch
        uuid_epoch = nanoseconds_100 + 0x01b21dd213814000
        v4_ts = v4.time

        assert uuid_epoch != v4_ts
        new_v4 = rewrite_uuid(v4_str, orig_str)

        assert uuid_epoch == new_v4.time


if __name__ == '__main__':
    unittest.main()
