import json
import logging
import os
import unittest

from confluent_kafka import Producer
from confluent_kafka import Consumer

from tests.base import BaseTestCase

logger = logging.getLogger(__name__)


class MyTestCase(BaseTestCase):

    config = None
    topic = 'events'

    data_key = None
    str_data = None

    json_data = None

    @classmethod
    def _set_up_class(cls):
        cls.config = {
            # User-specific properties that you must set
            'bootstrap.servers': os.getenv('kafka_bootstrap_servers'),
        }

        cls.str_data = cls.read_file_to_str('trace-01-part1.json')
        cls.json_data = json.loads(cls.str_data)
        for item in cls.json_data['batch']:
            cls.data_key = item['id']
            break

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(self, err, msg):
        if err:
            logger.error('ERROR: Message failed delivery: %s', err)
        else:
            topic = msg.topic()
            key = msg.key().decode('utf-8')
            value = msg.value().decode('utf-8')
            logger.info("Produced event to topic [%s]: key = %s, value = %s", topic, key, value)

    def send_events(self):
        send_config = {
            **self.config
            , 'acks': 'all'
        }

        logger.info("kafka_bootstrap_servers=%s", os.getenv('kafka_bootstrap_servers'))

        logger.info("send topic=[%s], key=[%s] events", self.topic, self.data_key)
        assert self.topic
        assert self.data_key

        producer = Producer(send_config)
        producer.produce(self.topic, self.str_data, self.data_key, callback=self.delivery_callback)

        # Block until the messages are sent.
        producer.poll(30)
        producer.flush(30)

    def test_receive_events(self):
        # send data
        self.send_events()

        receive_config = {
            **self.config
            , 'group.id': 'langfarm-consume-events'
            , 'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(receive_config)
        consumer.subscribe([self.topic])

        max_wait_cnt = 10
        wait_cnt = 0

        key = None
        value = None

        # Poll for new messages from Kafka and print them.
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    # Initial message consumption may take up to
                    # `session.timeout.ms` for the consumer group to
                    # rebalance and start consuming
                    wait_cnt += 1
                    logger.info("Waiting... %s cnt", wait_cnt)
                    if wait_cnt >= max_wait_cnt:
                        break
                elif msg.error():
                    logger.error("ERROR: %s", msg.error())
                else:
                    # Extract the (optional) key and value, and print.
                    topic = msg.topic()
                    key = msg.key().decode('utf-8')
                    value = msg.value().decode('utf-8')
                    logger.info("Consumed event from topic [%s]: key = %s, value = %s", topic, key, value)
                    break
        except KeyboardInterrupt:
            pass
        finally:
            # Leave group and commit final offsets
            consumer.close()

        # assert
        assert key
        assert value

        assert key == self.data_key
        assert value == self.str_data


if __name__ == '__main__':
    unittest.main()
