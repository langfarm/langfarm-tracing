import datetime
import logging
import os
import unittest

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

# 要在 from langfarm_tracing.core import db 之前，改下 settings 的路径
from tests.base import BaseTestCase

from langfarm_tracing.auth.key import fast_hashed_secret_key
from langfarm_tracing.core import db
from langfarm_tracing.schema.langfuse import ApiKey


logger = logging.getLogger(__name__)


class MyTestCase(BaseTestCase):

    def test_utc_to_local_time(self):
        # tzinfo=pytz.timezone('Asia/Shanghai')
        # time
        utc = datetime.datetime(
            2024, 11, 29, 15, 29, 54, 381000
            , tzinfo=datetime.UTC
        )
        utc_str = '2024-11-29 15:29:54'
        utc_format = utc.strftime('%Y-%m-%d %H:%M:%S')
        logger.info("utc_time=%s, f=%s", utc, utc_format)
        assert utc_str == utc_format

        local_time = utc.astimezone()
        local_time_str = '2024-11-29 23:29:54'
        local_time_format = local_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("local_time=%s, f=%s", local_time, local_time_format)
        assert local_time_str == local_time_format

    def assert_sk_in_env(self) -> str:
        sk = os.getenv('LANGFUSE_SECRET_KEY')
        if not sk:
            logger.error("Please set 'LANGFUSE_SECRET_KEY' in .env for test langfuse api_key fast_hashed_secret_key")
            assert False
        return sk

    def assert_salt_in_env(self) -> str:
        salt = os.getenv('SALT')
        if not salt:
            logger.error("Please set 'SALT' in .env for test langfuse api_key fast_hashed_secret_key")
            assert False
        return salt

    def assert_api_key(self, api_key: ApiKey, pk: str):
        assert pk
        assert api_key

        logger.info("id = %s", api_key.id)
        logger.info("pk = %s", api_key.public_key)
        logger.info("fast_hashed = %s", api_key.fast_hashed_secret_key)
        logger.info("created_at = %s", api_key.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        assert api_key.public_key == pk
        assert api_key.fast_hashed_secret_key

        sk = self.assert_sk_in_env()
        salt = self.assert_salt_in_env()
        fast_hashed = fast_hashed_secret_key(sk, salt)

        assert api_key.fast_hashed_secret_key == fast_hashed

    def assert_pk_in_env(self) -> str:
        pk = os.getenv('LANGFUSE_PUBLIC_KEY')
        if not pk:
            logger.error("Please set 'LANGFUSE_PUBLIC_KEY' in .env for test select langfuse api_key")
            assert False
        return pk

    def test_select_api_key(self):
        pk = self.assert_pk_in_env()

        # read first
        stmt = select(ApiKey).where(ApiKey.public_key == pk)

        api_key = db.read_first(stmt, ApiKey)
        assert api_key
        self.assert_api_key(api_key, pk)

        # read all
        for api_key in db.read_list(stmt, ApiKey):
            self.assert_api_key(api_key, pk)

    def test_show_create_api_key_sql(self):
        sql = CreateTable(ApiKey.__table__).compile(dialect=postgresql.dialect())
        logger.info("sql=%s", sql)
        assert str(sql).find('WITHOUT TIME ZONE') > 0


if __name__ == '__main__':
    unittest.main()
