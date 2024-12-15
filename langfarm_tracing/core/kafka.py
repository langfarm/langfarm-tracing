import logging

from confluent_kafka import Producer

from langfarm_tracing.core.config import settings

logger = logging.getLogger(__name__)

kafka_producer_config = {
    # User-specific properties that you must set
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
    , 'acks': 'all'
}


def get_kafka_producer() -> Producer:
    logger.info("KAFKA_BOOTSTRAP_SERVERS=%s", settings.KAFKA_BOOTSTRAP_SERVERS)
    return Producer(kafka_producer_config)
