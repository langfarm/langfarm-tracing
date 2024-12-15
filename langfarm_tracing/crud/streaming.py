import logging
from typing import Tuple

from confluent_kafka import Producer, Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient, SchemaReference, RegisteredSchema
from confluent_kafka.schema_registry.json_schema import JSONSerializer, JSONDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

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


class KafkaSink:

    def __init__(self, topic: str, schema_name: str = None):
        """
        :param topic:
        :param schema_name: 当 None 时使用 topic 。找 json_schema/<schema_name>-schema.json 文件
        """
        self.topic = topic
        self.schema_name = schema_name if schema_name else topic

        self.schema: str = read_schema_to_str(self.schema_name)

        logger.info("KAFKA_SCHEMA_REGISTRY_URL=%s, topic=%s", settings.KAFKA_SCHEMA_REGISTRY_URL, topic)
        schema_registry_client = SchemaRegistryClient(schema_registry_config)
        self.json_serializer = JSONSerializer(self.schema, schema_registry_client)

    def to_headers(self, header: dict) -> list[tuple]:
        headers: list[tuple] = []
        for k, v in header.items():
            headers.append((k, bytes(str(v), encoding='UTF-8')))

        return headers

    def send_trace_ingestion(self, key: str, data: dict, header: dict):
        headers = self.to_headers(header)
        post_data = self.json_serializer(data, SerializationContext(self.topic, MessageField.VALUE))
        producer.produce(
            topic=self.topic, key=key, value=post_data, headers=headers, callback=delivery_callback
        )

    def flush(self, timeout: float):
        producer.flush(timeout)


def headers_to_dict(headers: list) -> dict:
    header_map = {}
    for h in headers:
        header_map[h[0]] = h[1]

    return header_map


class KafkaMessage:

    def __init__(self, key: str, body: dict, header: dict):
        self.key = key
        self.body = body
        self.header = header


class KafkaSource:

    def __init__(self, topic: str, group_id: str, **kwargs):
        receive_config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
            # , 'schema.registry.url': settings.KAFKA_SCHEMA_REGISTRY_URL
            , 'group.id': group_id
            , 'auto.offset.reset': 'earliest'
            , **kwargs
        }

        self.topic = topic

        logger.info("KAFKA_BOOTSTRAP_SERVERS=%s, topic=%s, group_id=%s", settings.KAFKA_SCHEMA_REGISTRY_URL, topic, group_id)
        schema_registry_client = SchemaRegistryClient(schema_registry_config)
        self.registered_schema: RegisteredSchema = schema_registry_client.get_latest_version(f"{topic}-value")
        self.schema_str = self.registered_schema.schema.schema_str
        self.json_deserializer = JSONDeserializer(self.schema_str, schema_registry_client=schema_registry_client)

        consumer = Consumer(receive_config)
        consumer.subscribe([topic])
        self.consumer = consumer

    def poll_message(self, timeout) -> KafkaMessage | None:
        msg = self.consumer.poll(timeout)
        if msg is None:
            return None
        elif msg.error():
            logger.error("receive_message_error: %s", msg.error())
            return None
        else:
            key = msg.key().decode('utf-8')
            message = self.json_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            header = headers_to_dict(msg.headers())

            return KafkaMessage(key, message, header)

    def close(self):
        self.consumer.close()
