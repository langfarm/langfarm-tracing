import json
import logging
import unittest

from tests.base import BaseTestCase
from langfarm_tracing.crud.events import TraceHandler, SpanHandler, GenerationHandler, BaseEventHandler, events_dispose
from langfarm_tracing.crud.streaming import KafkaSource, KafkaMessage

logger = logging.getLogger(__name__)


class MockEventData:

    def __init__(self, event_id: str, body: dict, header: dict):
        self.event_id = event_id
        self.body = body
        self.header = header

    def __str__(self):
        return str({
            'key': self.event_id
            , 'body': self.body
            , 'header': self.header
        })


class MockTraceHandler(TraceHandler):

    def __init__(self):
        super().__init__('traces')
        self.event_data_list: list[MockEventData] = []

    def send_event_to_sink(self, event_id: str, key: str, body: dict, header: dict):
        logger.info("id=%s, key=%s, body = %s, header = %s", event_id, key, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MockSpanHandler(SpanHandler):

    def __init__(self):
        super().__init__('observations')
        self.event_data_list = []

    def send_event_to_sink(self, event_id: str, key: str, body: dict, header: dict):
        logger.info("id=%s, key=%s, body = %s, header = %s", event_id, key, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MockGenerationHandler(GenerationHandler):

    def __init__(self):
        super().__init__('observations')
        self.event_data_list = []

    def send_event_to_sink(self, event_id: str, key: str, body: dict, header: dict):
        logger.info("id=%s, key=%s, body = %s, header = %s", event_id, key, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MyTestCase(BaseTestCase):

    project_id = 'cm42wglph0006pmicl9y9o7r8'
    topics = ['traces', 'observations']
    kafka_sources: dict[str, KafkaSource] = {}

    @classmethod
    def _set_up_class(cls):
        for topic in cls.topics:
            group_id = f'test-langfarm-consume-{topic}'
            # 'latest'
            kafka_source = KafkaSource(topic, group_id, offset_reset='earliest')
            cls.kafka_sources[topic] = kafka_source

    @classmethod
    def tearDownClass(cls):
        for k, kafka_source in cls.kafka_sources.items():
            kafka_source.close()

    def sub_message_to_list(self, message_source: KafkaSource, max_msg_cnt: int) -> list[KafkaMessage]:
        msg_cnt = 0

        max_wait_cnt = 10
        wait_cnt = 0

        event_data_list: list[KafkaMessage] = []

        # Poll for new messages from Kafka and print them.
        try:
            while True:
                msg = message_source.poll_message(1.0)
                if msg is None:
                    # Initial message consumption may take up to
                    # `session.timeout.ms` for the consumer group to
                    # rebalance and start consuming
                    if msg_cnt >= max_msg_cnt:
                        break
                    wait_cnt += 1
                    logger.info("Waiting... %s cnt", wait_cnt)
                    if wait_cnt >= max_wait_cnt:
                        break
                else:
                    # Extract the (optional) key and value, and print.
                    msg_cnt += 1

                    logger.info("Consumed event from topic [%s]: cnt = %s, key = %s, value = %s, header = %s", msg_cnt,
                                message_source.topic, msg.key, msg.body, msg.header)

                    event_data_list.append(msg)

                    if msg_cnt >= max_msg_cnt:
                        break
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            pass

        return event_data_list

    def assert_receive_message(self, topic: str, message_map: dict[str, MockEventData]):
        kafka_source = self.kafka_sources[topic]

        messages = self.sub_message_to_list(kafka_source, len(message_map))

        # assert
        for event_data in messages:
            # assert 'id' in event_data.body
            assert 'event_id' in event_data.header
            assert event_data.header['event_id'] in message_map
            e_event = message_map[event_data.header['event_id']]
            logger.info('assert receive message, 实际 = %s, 期望 = %s', event_data, e_event)
            assert event_data.body['id'] == e_event.body['id']
            assert event_data.body['project_id'] == e_event.body['project_id']

            assert 'created_at' in event_data.body

            if 'name' in event_data.body:
                assert event_data.body['name'] == e_event.body['name']
            if 'trace_id' in event_data.body:
                assert event_data.body['trace_id'] == e_event.body['trace_id']

            if 'type' in event_data.body:
                assert event_data.body['type'] == e_event.body['type']

            # if 'timestamp' in event_data.header:
            #     assert event_data.header['timestamp'] == e_event.header['timestamp']

            # == e_event.body['updated_at']
            if 'created_at' in event_data.body:
                assert event_data.body['created_at'] == e_event.body['created_at']
            if 'updated_at' in event_data.body:
                assert event_data.body['updated_at'] == e_event.body['updated_at']

            # header
            assert 'event_type' in event_data.header
            assert event_data.header['event_type'] == e_event.header['event_type']
            assert event_data.header['event_id'] == e_event.header['event_id']

            # cal cost
            if 'calculated_input_cost' in event_data.body:
                assert event_data.body['calculated_input_cost'] == str(e_event.body['calculated_input_cost'])
                assert 'internal_model' in event_data.body
                assert 'internal_model_id' in event_data.body
            if 'calculated_output_cost' in event_data.body:
                assert event_data.body['calculated_output_cost'] == str(e_event.body['calculated_output_cost'])
            if 'calculated_total_cost' in event_data.body:
                assert event_data.body['calculated_total_cost'] == str(e_event.body['calculated_total_cost'])

            if 'parent_observation_id' in event_data.body:
                assert event_data.body['parent_observation_id'] == e_event.body['parent_observation_id']

    def event_dispose_raw(self) -> dict[str, dict]:
        trace_handler = MockTraceHandler()
        span_handler = MockSpanHandler()
        generation_handler = MockGenerationHandler()
        handlers: dict[str, BaseEventHandler] = {
            'trace-create': trace_handler
            , 'span-create': span_handler
            , 'span-update': span_handler
            , 'generation-create': generation_handler
            , 'generation-update': generation_handler
        }

        datas = [
            json.loads(self.read_file_to_str('trace-02-part1.json')),
            json.loads(self.read_file_to_str('trace-02-part2.json'))
        ]
        for data in datas:
            out = events_dispose(data, self.project_id, handlers)
            logger.info("mock dispose out => %s", out)
            errs = out.get('errors')
            assert len(errs) < 1

        expect_event_map = {}
        obs_map = {}
        for handler in [span_handler, generation_handler]:
            events = handler.event_data_list
            for event_obj in events:
                obs_map[event_obj.header['event_id']] = event_obj

        expect_event_map[self.topics[1]] = obs_map
        traces_map = {}
        for handler in [trace_handler]:
            events = handler.event_data_list
            for event_obj in events:
                traces_map[event_obj.header['event_id']] = event_obj

        expect_event_map[self.topics[0]] = traces_map
        return expect_event_map

    def test_events_dispose_raw(self):
        trace_timestamp = "2024-12-11T16:07:09.474776Z"
        new_trace_id = 'f9936670-b7d9-41ef-ab5b-db59cd617c24'
        prefix = 'f9936670-b7d9-41ef-'
        prefix_len = len(prefix)
        expect_event_map = self.event_dispose_raw()
        for k, v in expect_event_map.items():
            for _, event_obj in v.items():
                # logger.info('event_body = %s', event_obj.body)
                # 验证同一个 trace 相关的使用同时分区时间
                assert 'created_at' in event_obj.body
                assert event_obj.body['created_at'] == trace_timestamp
                # trace
                if 'trace-create' in event_obj.header['event_type']:
                    assert event_obj.body['id'] == new_trace_id
                else:
                    # observation
                    assert event_obj.body['trace_id'] == new_trace_id
                    assert event_obj.body['id'][:prefix_len] == prefix
                    if 'parent_observation_id' in event_obj.body:
                        assert event_obj.body['parent_observation_id'][:prefix_len] == prefix


    def test_events_dispose(self):
        expect_event_map = self.event_dispose_raw()

        datas = [
            json.loads(self.read_file_to_str('trace-02-part1.json')),
            json.loads(self.read_file_to_str('trace-02-part2.json'))
        ]

        for data in datas:
            out = events_dispose(data, self.project_id)
            logger.info("kafka dispose out => %s", out)
            errs = out.get('errors')
            assert len(errs) < 1

        for topic in self.topics:
            self.assert_receive_message(topic, expect_event_map[topic])

if __name__ == '__main__':
    unittest.main()
