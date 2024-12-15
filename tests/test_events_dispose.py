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
        super().__init__()
        self.event_data_list: list[MockEventData] = []

    def send_event_to_sink(self, event_id: str, body: dict, header: dict):
        logger.info("id=%s, body = %s, header = %s", event_id, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MockSpanHandler(SpanHandler):

    def __init__(self):
        super().__init__()
        self.event_data_list = []

    def send_event_to_sink(self, event_id: str, body: dict, header: dict):
        logger.info("id=%s, body = %s, header = %s", event_id, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MockGenerationHandler(GenerationHandler):

    def __init__(self):
        super().__init__()
        self.event_data_list = []

    def send_event_to_sink(self, event_id: str, body: dict, header: dict):
        logger.info("id=%s, body = %s, header = %s", event_id, body, header)
        self.event_data_list.append(MockEventData(event_id, body, header))


class MyTestCase(BaseTestCase):

    topics = ['traces', 'observations']
    kafka_sources: dict[str, KafkaSource] = {}

    @classmethod
    def _set_up_class(cls):
        for topic in cls.topics:
            group_id = f'test-langfarm-consume-{topic}'
            # 'latest'
            kafka_source = KafkaSource(topic, group_id)
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
            assert event_data.key in message_map
            e_event = message_map[event_data.key]
            logger.info('assert receive message, 实际 = %s, 期望 = %s', event_data, e_event)
            assert event_data.body['id'] == e_event.body['id']
            assert event_data.body['project_id'] == e_event.body['project_id']

            if 'name' in event_data.body:
                assert event_data.body['name'] == e_event.body['name']
            if 'trace_id' in event_data.body:
                assert event_data.body['trace_id'] == e_event.body['trace_id']

            if 'type' in event_data.body:
                assert event_data.body['type'] == e_event.body['type']

            # == e_event.body['updated_at']
            assert event_data.body['updated_at']

            # header
            assert 'event_type' in event_data.header
            assert event_data.header['event_type'] == e_event.header['event_type']

    def test_events_dispose(self):
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

        project_id = 'cm42wglph0006pmicl9y9o7r8'
        datas = [
            json.loads(self.read_file_to_str('trace-02-part1.json')),
            json.loads(self.read_file_to_str('trace-02-part2.json'))
        ]
        for data in datas:
            out = events_dispose(data, project_id, handlers)
            logger.info("mock dispose out => %s", out)

        expect_event_map = {}
        obs_map = {}
        for handler in [span_handler, generation_handler]:
            events = handler.event_data_list
            for event_obj in events:
                obs_map[event_obj.event_id] = event_obj

        expect_event_map[self.topics[1]] = obs_map
        traces_map = {}
        for handler in [trace_handler]:
            events = handler.event_data_list
            for event_obj in events:
                traces_map[event_obj.event_id] = event_obj

        expect_event_map[self.topics[0]] = traces_map
        datas = [
            json.loads(self.read_file_to_str('trace-02-part1.json')),
            json.loads(self.read_file_to_str('trace-02-part2.json'))
        ]
        for data in datas:
            out = events_dispose(data, project_id)
            logger.info("kafka dispose out => %s", out)

        for topic in self.topics:
            self.assert_receive_message(topic, expect_event_map[topic])


if __name__ == '__main__':
    unittest.main()
