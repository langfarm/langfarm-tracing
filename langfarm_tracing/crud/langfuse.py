from datetime import datetime

from sqlalchemy import select, or_, text, nullslast

from langfarm_tracing.auth import key
from langfarm_tracing.core import db
from langfarm_tracing.core.config import settings
from langfarm_tracing.schema.langfuse import ApiKey, Model


def select_api_key_by_pk_sk(pk: str, sk: str) -> ApiKey | None:
    fast_hashed_secret_key = key.fast_hashed_secret_key(sk, settings.SALT)
    stmt = (
        select(ApiKey)
        .where(ApiKey.fast_hashed_secret_key == fast_hashed_secret_key)
        .where(ApiKey.public_key == pk)
    )
    api_key = db.read_first(stmt, ApiKey)
    return api_key

def find_model(model: str, project_id: str, unit: str = None) -> Model | None:
    start_time = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S%z')
    start_time_where = text(f"start_date <= '{start_time}'::timestamp with time zone at time zone 'UTC'")
    stmt = (
        select(Model)
        .where(or_(Model.project_id == project_id, Model.project_id.is_(None)))
        .where(text(":model ~ match_pattern").params({"model": model}))
        .where(or_(start_time_where, Model.start_date.is_(None)))
        .order_by(Model.project_id.asc())
        .order_by(nullslast(Model.start_date.desc()))
        .limit(1)
    )

    if unit:
        stmt = stmt.where(Model.unit == unit)

    model = db.read_first(stmt, Model)
    return model
