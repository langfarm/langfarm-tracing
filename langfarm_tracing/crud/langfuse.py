from sqlalchemy import select

from langfarm_tracing.auth import key
from langfarm_tracing.core import db
from langfarm_tracing.core.config import settings
from langfarm_tracing.schema.langfuse import ApiKey


def select_api_key_by_pk_sk(pk: str, sk: str) -> ApiKey | None:
    fast_hashed_secret_key = key.fast_hashed_secret_key(sk, settings.SALT)
    stmt = (
        select(ApiKey)
        .where(ApiKey.fast_hashed_secret_key == fast_hashed_secret_key)
        .where(ApiKey.public_key == pk)
    )
    api_key = db.read_first(stmt, ApiKey)
    return api_key
