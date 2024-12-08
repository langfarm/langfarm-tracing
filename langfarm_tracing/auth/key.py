import base64
import hashlib


def decode_from_basic_auth(authorization: str) -> (str | None, str | None):
    """
    从 http 的 basic_auth 内容解码出 public key 和 secret key
    :param authorization: http 的 basic_auth head 'authorization'
    :return: (pk, sk)
    """
    pk = None
    sk = None
    auth = authorization.split(' ')
    if len(auth) > 1:
        auth = base64.b64decode(auth[1]).decode()
        auth = auth.split(':')
        pk = auth[0]
        if len(auth) > 1:
            sk = auth[1]
    return pk, sk


def fast_hashed_secret_key(secret_key: str, salt: str) -> str:
    """
    兼容 langfuse secret_key 的 hash 算法。
    :param secret_key: langfuse 生成的 secret_key
    :param salt: langfuse 的 'SALT' 环境变量
    :return: fast hashed 的 secret_key 等同于 langfuse 的 api_keys.fast_hashed_secret_key 字段值。
    """
    # 计算 盐
    _salt = hashlib.sha256()
    _salt.update(salt.encode('utf-8'))
    salt_hash = _salt.hexdigest()

    # sk 加 盐
    sk = hashlib.sha256()
    sk.update(secret_key.encode())
    sk.update(salt_hash.encode())

    return sk.hexdigest()
