import decimal
import json
import logging

from confluent_kafka import Consumer

from langfarm_tracing.core.config import settings
from langfarm_tracing.core.kafka import get_kafka_producer

logger = logging.getLogger(__name__)


def delivery_callback(err, msg):
    if err:
        logger.error('ERROR: Message failed delivery: %s', err)
    elif logger.isEnabledFor(logging.DEBUG):
        topic = msg.topic()
        key = msg.key().decode('utf-8')
        # value = msg.value().decode('utf-8')
        logger.debug("send event to topic [%s]: key = %s", topic, key)


schema_dir = __file__[:-len('/streaming.py')]


def read_schema_to_str(schema_name: str) -> str:
    """
    读取 json-schema 的文本内容
    :param schema_name: json-schema 的名
    :return: str
    """
    with open(f"{schema_dir}/json_schema/{schema_name}-schema.json") as f:
        return f.read()


schema_registry_config = {
    'url': settings.KAFKA_SCHEMA_REGISTRY_URL,
}

producer = get_kafka_producer()



class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


class KafkaSink:

    def __init__(self, topic: str, schema_name: str = None):
        """
        :param topic:
        :param schema_name: 当 None 时使用 topic 。找 json_schema/<schema_name>-schema.json 文件
        """
        self.topic = topic
        self.schema_name = schema_name if schema_name else topic

        self.schema: str = read_schema_to_str(self.schema_name)

    def to_headers(self, header: dict) -> list[tuple]:
        headers: list[tuple] = []
        for k, v in header.items():
            headers.append((k, bytes(str(v), encoding='UTF-8')))

        return headers

    def send_trace_ingestion(self, key: str, data: dict, header: dict):
        headers = self.to_headers(header)
        post_data = json.dumps(data, ensure_ascii=False, cls=DecimalEncoder)
        producer.produce(
            topic=self.topic, key=key, value=post_data, headers=headers, callback=delivery_callback
        )

    def flush(self, timeout: float):
        producer.flush(timeout)


def headers_to_dict(headers: list) -> dict:
    header_map = {}
    for h in headers:
        header_map[h[0]] = h[1].decode('utf-8')

    return header_map


class KafkaMessage:

    def __init__(self, key: str, body: dict, header: dict):
        self.key = key
        self.body = body
        self.header = header

    def __str__(self):
        return str({
            'key': self.key
            , 'body': self.body
            , 'header': self.header
        })


class KafkaSource:

    def __init__(self, topic: str, group_id: str, offset_reset: str = 'latest'):
        """
        kafka 消息消费
        :param topic: 主题
        :param group_id: 消耗组 id
        :param offset_reset: 'earliest' or 'latest'。默认 'latest'
        """
        receive_config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
            , 'group.id': group_id
            , 'auto.offset.reset': offset_reset
        }

        self.receive_config = receive_config
        self.topic = topic
        self.group_id = group_id

        logger.info("receive_config = %s", receive_config)

        consumer = Consumer(receive_config)
        consumer.subscribe([topic])
        self.consumer = consumer

    def poll_message(self, timeout) -> KafkaMessage | None:
        msg = self.consumer.poll(timeout)
        if msg is None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("poll message is null within timeout = %s, receive_config = %s", timeout, self.receive_config)
            return None
        elif msg.error():
            logger.error("receive_message_error: %s", msg.error())
            return None
        else:
            key = msg.key().decode('utf-8')
            message = json.loads(msg.value().decode('utf-8'))
            header = headers_to_dict(msg.headers())

            return KafkaMessage(key, message, header)

    def close(self):
        self.consumer.close()
        logger.info("Consumer close! topic = %s, group_id = %s", self.topic, self.group_id)
