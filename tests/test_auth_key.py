import unittest

from langfarm_tracing.auth import key
from tests.base import BaseTestCase


class MyTestCase(BaseTestCase):

    def test_decode_from_basic_auth(self):
        my_pk = 'this_is_pk'
        my_sk = 'this_is_sk'
        authorization = 'Basic dGhpc19pc19wazp0aGlzX2lzX3Nr'
        pk, sk = key.decode_from_basic_auth(authorization)
        assert pk
        assert pk == my_pk

        assert sk
        assert sk == my_sk

        # is only pk
        authorization = 'Basic dGhpc19pc19waw=='
        pk, sk = key.decode_from_basic_auth(authorization)
        assert pk
        assert pk == my_pk

        assert sk is None

        # is pk, sk is blank
        authorization = 'Basic dGhpc19pc19wazo='
        pk, sk = key.decode_from_basic_auth(authorization)
        assert pk
        assert pk == my_pk

        assert sk == ''


if __name__ == '__main__':
    unittest.main()
