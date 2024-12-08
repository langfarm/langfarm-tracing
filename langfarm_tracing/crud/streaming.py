import logging

from confluent_kafka import Producer

from langfarm_tracing.core.config import settings

logger = logging.getLogger(__name__)


def delivery_callback(err, msg):
    if err:
        logger.error('ERROR: Message failed delivery: %s', err)
    elif logger.isEnabledFor(logging.DEBUG):
        topic = msg.topic()
        key = msg.key().decode('utf-8')
        # value = msg.value().decode('utf-8')
        logger.debug("send event to topic [%s]: key = %s", topic, key)


class KafkaSink:

    def __init__(self, topic: str):
        _config = {
            # User-specific properties that you must set
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
            , 'acks': 'all'
        }

        logger.info("KAFKA_BOOTSTRAP_SERVERS=%s", settings.KAFKA_BOOTSTRAP_SERVERS)
        self.config = _config
        self.topic = topic
        self.producer = Producer(_config)

    def send_trace_ingestion(self, key: str, data: str):
        self.producer.produce(self.topic, data, key, callback=delivery_callback)

    def flush(self, timeout: float):
        self.producer.flush(timeout)
