import hashlib


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
