import json
import logging
from abc import abstractmethod
from datetime import datetime, timezone

from langfarm_tracing.crud.streaming import KafkaSink

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


class BaseEventHandler:

    def __init__(self, topic: str):
        self.topic = topic
        self.kafka_sink = KafkaSink(topic)
        self.schema_json = json.loads(self.kafka_sink.schema)

    def topic_name(self) -> str:
        return self.topic

    def _deal_created_at(self, body: dict, start_time_key: str):
        if start_time_key in body:
            body[start_time_key] = format_datetime(utc_time_to_ltz(body[start_time_key]))
            created_at = format_datetime(datetime.now())
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

    def handle_event(self, project_id: str, body: dict, event: dict, header: dict) -> dict:
        body['project_id'] = project_id
        body['updated_at'] = format_datetime(datetime.now())

        result = self._do_handle_event(project_id, body, event)

        self.remove_key_not_in_schema(result)

        return result

    def send_event_to_sink(self, event_id: str, body: dict, header: dict):
        try:
            self.kafka_sink.send_trace_ingestion(event_id, body, header)
        except Exception as e:
            logger.error("send_trace_error id=%s, err: %s, body = %s", event_id, e, body)
            raise e


class TraceHandler(BaseEventHandler):

    def __init__(self):
        super().__init__('traces')

    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        obj_transform_str(body, 'input')
        obj_transform_str(body, 'output')
        obj_transform_str(body, 'metadata')

        super()._deal_created_at(body, 'timestamp')

        # rename
        super()._rename_key(body, 'userId', 'user_id')
        super()._rename_key(body, 'sessionId', 'session_id')

        return body


class SpanHandler(BaseEventHandler):

    def __init__(self):
        super().__init__('observations')

    def _do_handle_event(self, project_id: str, body: dict, event: dict) -> dict:
        obj_transform_str(body, 'input')
        obj_transform_str(body, 'output')
        obj_transform_str(body, 'metadata')

        body['type'] = 'SPAN'

        super()._deal_created_at(body, 'startTime')

        if 'endTime' in body:
            body['endTime'] = format_datetime(utc_time_to_ltz(body['endTime']))

        # rename
        super()._rename_key(body, 'traceId', 'trace_id')
        super()._rename_key(body, 'startTime', 'start_time')
        super()._rename_key(body, 'statusMessage', 'status_message')
        super()._rename_key(body, 'parentObservationId', 'parent_observation_id')
        super()._rename_key(body, 'endTime', 'end_time')

        return body


class GenerationHandler(SpanHandler):

    def _deal_usage(self, body: dict):
        if 'usage' in body:
            usage = body['usage']
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            if 'input' in usage:
                prompt_tokens = usage['input']
            if 'output' in usage:
                completion_tokens = usage['output']
            if 'total' in usage:
                total_tokens = usage['total']

            if 'unit' in usage:
                body['unit'] = usage['unit']

            input_cost = 0
            output_cost = 0
            total_cost = 0
            if 'inputCost' in usage:
                input_cost = usage['inputCost']
            if 'outputCost' in usage:
                output_cost = usage['outputCost']
            if 'totalCost' in usage:
                total_cost = usage['totalCost']
            else:
                total_cost = input_cost + output_cost

            body['total_cost'] = total_cost

            # other
            if 'promptTokens' in usage:
                prompt_tokens = usage['promptTokens']
            if 'completionTokens' in usage:
                completion_tokens = usage['completionTokens']
            if 'totalTokens' in usage:
                total_tokens = usage['totalTokens']

            if total_tokens < 1:
                total_tokens = prompt_tokens + completion_tokens

            # fill
            body['prompt_tokens'] = prompt_tokens
            body['completion_tokens'] = completion_tokens
            body['total_tokens'] = total_tokens

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


trace_handler = TraceHandler()
span_handler = SpanHandler()
generation_handler = GenerationHandler()
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
    # header = json.dumps(header, ensure_ascii=False)
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
            header = top_header.copy()
            header['event_type'] = event_type
            if 'timestamp' in event:
                header['timestamp'] = format_datetime(utc_time_to_ltz(event['timestamp']))

            try:
                # 处理 event
                message = handler.handle_event(project_id, body, event, header)

                # send to kafka
                handler.send_event_to_sink(event_id, message, header)
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
