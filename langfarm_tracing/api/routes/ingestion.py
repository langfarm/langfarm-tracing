import json
import logging

from cachetools import cached, TTLCache
from fastapi import APIRouter, Header, HTTPException, Depends

from langfarm_tracing.auth import key

from langfarm_tracing.crud.events import events_dispose
from langfarm_tracing.crud.langfuse import select_api_key_by_pk_sk, find_model as _find_model
from langfarm_tracing.schema.langfuse import ApiKey, Model

logger = logging.getLogger(__name__)

router = APIRouter()

# 10 分钟 + 256 容量
@cached(cache=TTLCache(maxsize=256, ttl=600), info=True)
def get_api_key_by_cache(pk: str, sk: str) -> ApiKey:
    api_key = select_api_key_by_pk_sk(pk, sk)
    return api_key


@cached(cache=TTLCache(maxsize=256, ttl=600), info=True)
def find_model_by_cache(model_name: str, project_id: str, unit: str = None) -> Model | None:
    return _find_model(model_name, project_id, unit=unit)


async def basic_auth(authorization: str = Header()) -> ApiKey:
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
    return api_key


def cache_info_to_dict(_cache_info) -> dict:
    return {
        'hits': _cache_info[0]
        , 'misses': _cache_info[1]
        , 'maxsize': _cache_info[2]
        , 'currsize': _cache_info[3]
    }


def create_cache_info(_cache_handler, clear_cache: bool = False):
    info = cache_info_to_dict(_cache_handler.cache_info())
    if clear_cache:
        _cache_handler.cache_clear()
        after_info = cache_info_to_dict(_cache_handler.cache_info())
        logger.info("clear_cache[api_key], before=%s, after=%s", info, after_info)
        info = after_info
    return info


named_cache = {
    'api_key': get_api_key_by_cache
    , 'model': find_model_by_cache
}


@router.get("/cache_info")
async def cache_info(name: str = None, clear_cache: bool = False):
    name_list = []
    if name in named_cache:
        name_list.append(name)
    else:
        name_list.extend(named_cache.keys())

    named_info = {}
    for name in name_list:
        named_info[name] = create_cache_info(named_cache[name], clear_cache)

    return named_info


@router.get("/find_model")
async def find_model(model_name: str, unit: str = None, api_key: ApiKey = Depends(basic_auth)):
    project_id = api_key.project_id
    return find_model_by_cache(model_name, project_id, unit=unit)


@router.post("/")
async def trace_ingestion(data: dict, api_key: ApiKey = Depends(basic_auth)):
    """
    接收 Langfuse 客户端的 trace 上报
    :param data: tracing 内容
    :param api_key: 从 header 的 authorization 取出 pk, sk 在 db 里找到 api_key 的记录。
    :return: {"successes": {"id": "xxx", "status": 201}, "errors": []}
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("/api/public/ingestion => \n%s", json.dumps(data, ensure_ascii=False, indent=4))

    # 取 project_id
    project_id = api_key.project_id
    out = events_dispose(data, project_id)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("out => %s", out)
    return out
