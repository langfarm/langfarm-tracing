import json
import logging
from abc import abstractmethod
from datetime import datetime, timezone
from typing import final

from langfarm_tracing.core.redis import read_created_at_or_set
from langfarm_tracing.crud.langfuse import find_model_by_cache
from langfarm_tracing.crud.streaming import KafkaSink
from langfarm_tracing.schema.langfuse import Model

logger = logging.getLogger(__name__)


def obj_transform_str(body: dict, key: str):
    if key in body:
        _input = body[key]
        if isinstance(_input, (dict, list)):
            body[key] = json.dumps(_input, ensure_ascii=False)


def utc_time_to_ltz(utc_str: str) -> datetime:
    utc = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    ltz = utc.replace(tzinfo=timezone.utc).astimezone()
    return ltz


def format_datetime(dt: datetime) -> str:
    return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S.%f')


def created_at_to_suffix_id(utc_str: str) -> str:
    ltz = utc_time_to_ltz(utc_str)
    # return datetime.strftime(ltz, '%Y%m%d%H')
    # 使用Unix时间戳（秒）
    return str(int(ltz.timestamp()))


class BaseEventHandler:

    def __init__(self, topic: str, schema_name: str = None):
        self.topic = topic
        self.kafka_sink = KafkaSink(topic, schema_name)
        self.schema_json = json.loads(self.kafka_sink.schema)

    def topic_name(self) -> str:
        return self.topic

    def _deal_created_at(self, body: dict, start_time_key: str, event: dict):
        if start_time_key in body:
            # 使用原本的格式 string data-time with utc
            if 'timestamp' in event:
                created_at = event['timestamp']
                body['created_at'] = created_at
                body['updated_at'] = created_at

    def _rename_key(self, body: dict, old_key: str, new_key:str):
        if old_key in body:
            v = body.pop(old_key)
            body[new_key] = v

    def remove_key_not_in_schema(self, body: dict):
        remove_keys = []
        for k in body:
            if k not in self.schema_json['properties']:
                remove_keys.append(k)

        for k in remove_keys:
            del body[k]

    @abstractmethod
    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        pass

    @final
    def handle_event(self, project_id: str, body: dict, event: dict, header: dict) -> dict:
        # 备份原始 id 和 traceId
        body['__id__'] = body['id']
        if 'traceId' in body:
            body['__trace_id__'] = body['traceId']
        body['project_id'] = project_id

        result = self._do_handle_event(project_id, body, event)

        self.remove_key_not_in_schema(result)

        return result

    def dump_origin_trace_id(self, body: dict) -> str | None:
        # 抽取原始 trace_id
        if '__trace_id__' in body:
            return body['__trace_id__']
        else:
            return None

    def dump_origin_body_id(self, body: dict) -> str:
        if '__id__' in body:
            _id = body['__id__']
        else:
            _id = body['id']
        return _id

    def create_redis_key_body_id(self, origin_body_id: str) -> str:
        return f"{self.topic}-{origin_body_id}"

    def create_redis_key_trace_id(self, origin_trace_id) -> str:
        return f"traces-{origin_trace_id}"

    def create_new_id(self, origin_id: str, created_at: str) -> str:
        """
        按 created_at 重新生成 id。格式如 '35d534a3-e8b6-41e0-9554-e835d41b15a9' 的最后一段按成 created_at 的时间戳（秒）
        :param origin_id: 原始 id
        :param created_at: 一般是 langfuse 上报的 timestamp
        :return: 格式如 '35d534a3-e8b6-41e0-9554-1735316902'
        """
        return f"{origin_id[:23]}-{created_at_to_suffix_id(created_at)}"

    def reset_body_id(self, body: dict, origin_body_id: str, created_at: str) -> str:
        body_id = self.create_new_id(origin_body_id, created_at)
        body['id'] = body_id
        return body_id

    def reset_trace_id(self, body: dict, origin_trace_id: str, created_at: str):
        if '__trace_id__' in body:
            body['trace_id'] = self.create_new_id(origin_trace_id, created_at)

    def reset_parent_observation_id(self, body: dict, origin_parent_observation_id, created_at: str):
        if 'parent_observation_id' in body:
            body['__parent_id__'] = body['parent_observation_id']
            body['parent_observation_id'] = self.create_new_id(origin_parent_observation_id, created_at)

    def send_event_to_sink(self, event_id: str, key: str, body: dict, header: dict):
        try:
            self.kafka_sink.send_trace_ingestion(key, body, header)
        except Exception as e:
            logger.error("send_trace_error id=%s, key=%s, err: %s, body = %s", event_id, key, e, body)
            raise e


class TraceHandler(BaseEventHandler):

    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        obj_transform_str(body, 'input')
        obj_transform_str(body, 'output')
        obj_transform_str(body, 'metadata')

        super()._deal_created_at(body, 'timestamp', event)

        # rename
        super()._rename_key(body, 'userId', 'user_id')
        super()._rename_key(body, 'sessionId', 'session_id')

        return body


class SpanHandler(BaseEventHandler):

    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        obj_transform_str(body, 'input')
        obj_transform_str(body, 'output')
        obj_transform_str(body, 'metadata')

        body['type'] = 'SPAN'

        super()._deal_created_at(body, 'startTime', event)

        # rename
        super()._rename_key(body, 'traceId', 'trace_id')
        super()._rename_key(body, 'startTime', 'start_time')
        super()._rename_key(body, 'statusMessage', 'status_message')
        super()._rename_key(body, 'parentObservationId', 'parent_observation_id')
        super()._rename_key(body, 'endTime', 'end_time')

        return body


class GenerationHandler(SpanHandler):

    def _find_model(self, body: dict, usage: dict) -> Model | None:
        unit = None

        model = None
        if 'unit' in usage:
            unit = usage['unit']
        if 'model' in body and 'project_id' in body:
            model_name = body['model']
            project_id = body['project_id']
            model = find_model_by_cache(model_name, project_id, unit)

        return model

    def _deal_input_usage(self, usage: dict) -> (int, int, int):
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if 'input' in usage:
            prompt_tokens = usage['input']
        if 'output' in usage:
            completion_tokens = usage['output']
        if 'total' in usage:
            total_tokens = usage['total']
        else:
            total_tokens = prompt_tokens + completion_tokens

        return prompt_tokens, completion_tokens, total_tokens


    def _deal_usage(self, body: dict):
        if 'usage' in body:
            usage = body['usage']
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            total_cost = 0
            if 'input' in usage:
                prompt_tokens, completion_tokens, total_tokens = self._deal_input_usage(usage)
                if 'unit' in usage:
                    body['unit'] = usage['unit']

                input_cost = 0
                output_cost = 0
                if 'inputCost' in usage:
                    input_cost = usage['inputCost']
                if 'outputCost' in usage:
                    output_cost = usage['outputCost']
                if 'totalCost' in usage:
                    total_cost = usage['totalCost']
                else:
                    total_cost = input_cost + output_cost
            else:
                # other, 与 input/output 二选一
                if 'promptTokens' in usage:
                    prompt_tokens = usage['promptTokens']
                if 'completionTokens' in usage:
                    completion_tokens = usage['completionTokens']
                if 'totalTokens' in usage:
                    total_tokens = usage['totalTokens']
                else:
                    total_tokens = prompt_tokens + completion_tokens

            # fill
            body['prompt_tokens'] = prompt_tokens
            body['completion_tokens'] = completion_tokens
            body['total_tokens'] = total_tokens

            if total_cost:
                # 用户上报 cost
                body['total_cost'] = total_cost
            else:
                # 计算 cost
                model = self._find_model(body, usage)
                if model:
                    calculated_input_cost = prompt_tokens * model.input_price
                    calculated_output_cost = completion_tokens * model.output_price
                    if model.total_price:
                        calculated_total_cost = total_tokens * model.total_price
                    else:
                        calculated_total_cost = calculated_input_cost + calculated_output_cost

                    # add body
                    body['calculated_input_cost'] = calculated_input_cost
                    body['calculated_output_cost'] = calculated_output_cost
                    body['calculated_total_cost'] = calculated_total_cost
                    # add model info
                    body['internal_model'] = model.model_name
                    body['internal_model_id'] = model.id


    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        super()._do_handle_event(project_id, body, event)

        body['type'] = 'GENERATION'

        # usage
        self._deal_usage(body)

        # model
        if 'modelParameters' in body:
            body['modelParameters'] = json.dumps(body['modelParameters'], ensure_ascii=False)

        # rename
        super()._rename_key(body, 'completionStartTime', 'completion_start_time')
        super()._rename_key(body, 'promptName', 'prompt_mame')
        super()._rename_key(body, 'promptVersion', 'prompt_version')

        return body


trace_handler = TraceHandler('traces')
span_handler = SpanHandler('observations')
generation_handler = GenerationHandler('observations')
handlers: dict[str, BaseEventHandler] = {
    'trace-create': trace_handler
    , 'span-create': span_handler
    , 'span-update': span_handler
    , 'generation-create': generation_handler
    , 'generation-update': generation_handler
}


def dump_event_header(data: dict) -> dict:
    header = data.get('metadata', {})
    if 'batch_size' in header:
        del header['batch_size']
    if not isinstance(header, dict):
        try:
            header = json.loads(str(header))
        except Exception as e:
            header = {}

    return header


def events_dispose(data: dict, project_id: str, handler_map: dict = None) -> dict:
    if handler_map is None:
        handler_map = handlers
    # 取 top metadata
    top_header = dump_event_header(data)
    # 取到 batch
    batch = data.get('batch', [])
    successes = []
    errors = []
    for event in batch:
        if 'id' in event:
            event_id = str(event['id'])
            event_type = event['type']

            handler = handler_map.get(event_type, None)
            if not handler:
                errors.append({'id': event_id, 'status': 501, 'message': f'没有找到 [{event_type}] event handler'})
                continue

            body = event['body']
            # 没有 id 的 body 丢掉
            if 'id' not in body:
                errors.append({'id': event_id, 'status': 400, 'message': f'没有找到 body.id'})
                logger.warning('event=[%s], 没有找到 body.id, 此事件丢掉。', event_id)
                continue
            if 'timestamp' not in event:
                errors.append({'id': event_id, 'status': 400, 'message': f'event 没有找到 timestamp'})
                logger.warning('event=[%s], event 没有找到 timestamp, 此事件丢掉。', event_id)
                continue

            # 事件时间
            timestamp = event['timestamp']
            body['updated_at'] = timestamp

            # event_type 加 header
            header = top_header.copy()
            header['event_id'] = event_id
            header['event_type'] = event_type

            try:
                # 处理 event
                message = handler.handle_event(project_id, body, event, header)

                # 取得原始 body.id，用于生成带时间后缀的 body.id，
                _body_id = handler.dump_origin_body_id(body)

                # 重新设置 observations 的 trace_id
                trace_id = handler.dump_origin_trace_id(body)
                key = trace_id
                if trace_id:
                    # observations 数据
                    redis_trace_id_key = handler.create_redis_key_trace_id(trace_id)
                    # 用第一次接收到 timestamp 来生成 created_at
                    trace_created_at = read_created_at_or_set(redis_trace_id_key, timestamp)
                    handler.reset_trace_id(body, trace_id, trace_created_at)

                    # body.id 的时间后缀也使用 trace 的 created_at
                    # 下游表按时间分区时，数据落在与 trace 同一分区。
                    handler.reset_body_id(body, _body_id, trace_created_at)
                else:
                    # 此时是 traces 数据
                    redis_body_id_key = handler.create_redis_key_body_id(_body_id)
                    trace_created_at = read_created_at_or_set(redis_body_id_key, timestamp)
                    handler.reset_body_id(body, _body_id, trace_created_at)

                    key = _body_id

                # reset parent_observation_id
                if 'parent_observation_id' in body:
                    _parent_id = body['parent_observation_id']
                    redis_parent_id_key = handler.create_redis_key_body_id(_parent_id)
                    parent_created_at = read_created_at_or_set(redis_parent_id_key, timestamp)
                    handler.reset_parent_observation_id(body, _parent_id, parent_created_at)

                # send to kafka
                # 用 trace_id 作为 key
                handler.send_event_to_sink(event_id, key, message, header)
                # 已发送
                successes.append({'id': event_id, 'status': 201})
            except Exception as e:
                errors.append({
                    'id': event_id, 'status': 500
                    , 'message': f'发送 event[id={event_id}] 失败， type=[{event_type}]'
                    , 'error': str(e)
                })

    result = {"successes": successes, "errors": errors}
    return result
