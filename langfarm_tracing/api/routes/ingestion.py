import json
import logging
from functools import lru_cache

from fastapi import APIRouter, Header, HTTPException, Depends

from langfarm_tracing.auth import key
from langfarm_tracing.crud.langfuse import select_api_key_by_pk_sk
from langfarm_tracing.schema.langfuse import ApiKey

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache()
def get_api_key_by_cache(pk: str, sk: str) -> ApiKey:
    api_key = select_api_key_by_pk_sk(pk, sk)
    return api_key


async def basic_auth(authorization: str = Header()):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")

    # decode pk, sk
    pk, sk = key.decode_from_basic_auth(authorization)
    if pk is None:
        raise HTTPException(status_code=401, detail="Invalid credentials. Please configured username.")
    if sk is None:
        raise HTTPException(status_code=401, detail="Invalid credentials. Please configured password.")

    # get api_key
    api_key = get_api_key_by_cache(pk, sk)
    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid credentials. Please configured the correct authorization.")


def cache_info_to_dict(_cache_info) -> dict:
    return {
        'hits': _cache_info[0]
        , 'misses': _cache_info[1]
        , 'maxsize': _cache_info[2]
        , 'currsize': _cache_info[3]
    }


@router.get("/ingestion/cache_info")
async def cache_info(clear_cache: bool = False):
    info = cache_info_to_dict(get_api_key_by_cache.cache_info())
    if clear_cache:
        get_api_key_by_cache.cache_clear()
        after_info = cache_info_to_dict(get_api_key_by_cache.cache_info())
        logger.info("clear_cache[api_key], before=%s, after=%s", info, after_info)
        info = after_info
    return info


@router.post("/ingestion", dependencies=[Depends(basic_auth)])
async def trace_ingestion(data: dict):
    """
    接收 Langfuse 客户端的 trace 上报
    :param data: trace 内容
    :return: {"successes": {"id": "xxx", "status": 201}, "errors": []}
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("/api/public/ingestion => \n%s", json.dumps(data, ensure_ascii=False, indent=4))
    batch = data.get('batch', [])
    results = []
    for event in batch:
        results.append({
            'id': event['id']
            , 'status': 201
        })

    out = {"successes": results, "errors": []}
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("out => %s", out)
    return out
