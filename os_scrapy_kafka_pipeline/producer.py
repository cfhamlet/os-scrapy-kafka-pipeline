import logging
import threading
from typing import Dict, List, Optional

from expiringdict import ExpiringDict
from kafka.producer import KafkaProducer

DEFAULT_FLAG = "__DEFAULT__"

KAFKA_LOGGERS = [
    "kafka.conn",
    "kafka.client",
    "kafka.producer.kafka",
    "kafka.protocol.parser",
    "kafka.producer.sender",
    "kafka.cluster",
    "kafka.producer.record_accumulator",
    "kafka.metrics.metrics",
]


def set_kafka_loglevel(loglevel: int):
    for l in KAFKA_LOGGERS:
        logging.getLogger(l).setLevel(loglevel)


def get_brokers(boostrap_server: str) -> List[str]:
    producer = KafkaProducer(bootstrap_servers=[boostrap_server])
    return get_brokers_from_producer(producer)


def get_brokers_from_producer(producer: KafkaProducer) -> List[str]:
    producer._sender.run_once()
    brokers = producer._metadata.brokers()
    producer.close()
    return [f"{broker.host}:{broker.port}" for broker in brokers]


class AutoProducer(object):
    def __init__(
        self,
        bootstrap_servers=None,
        configs=None,
        topic=None,
        kafka_loglevel=logging.WARNING,
    ):
        set_kafka_loglevel(kafka_loglevel)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.lock = threading.Lock()

        self.topic: Optional[str] = topic
        configs = {} if configs is None else configs
        self.configs: dict = configs
        self.producers: Dict[str, KafkaProducer] = {}
        self.fail_pass = ExpiringDict(max_len=10000, max_age_seconds=60)

        bs = configs.pop("bootstrap_servers", None)
        if bootstrap_servers is None:
            bootstrap_servers = bs

        if bootstrap_servers:
            producer = self.get_producer(bootstrap_servers)
            if producer is None:
                raise Exception("can not init default producer")
            self.producers[DEFAULT_FLAG] = producer
        else:
            self.logger.warning("no default kafka producer")

    def send(
        self,
        topic=None,
        value=None,
        key=None,
        headers=None,
        partition=None,
        timestamp_ms=None,
        bootstrap_servers=None,
    ):
        producer = self.get_producer(
            bootstrap_servers if bootstrap_servers is not None else [DEFAULT_FLAG]
        )
        if producer is None:
            raise Exception("no available producer")

        topic = topic if topic is not None else self.topic
        if topic is None:
            raise Exception("no topic")

        return producer.send(
            topic,
            value=value,
            key=key,
            headers=headers,
            partition=partition,
            timestamp_ms=timestamp_ms,
        )

    def get_producer(self, boostrap_servers: List[str]) -> Optional[KafkaProducer]:
        with self.lock:
            return self._get_producer(boostrap_servers)

    def _get_producer(self, bootstrap_servers: List[str]) -> Optional[KafkaProducer]:
        for bootstrap_server in bootstrap_servers:
            if bootstrap_server in self.producers:
                return self.producers[bootstrap_server]
            if bootstrap_server == DEFAULT_FLAG:
                return None
            if bootstrap_server in self.fail_pass:
                continue
            try:
                brokers = get_brokers(bootstrap_server)
                self.logger.debug(f"brokers from {bootstrap_server} {brokers}")
            except Exception as e:
                self.logger.warning(f"can not get brokers {bootstrap_server} {e}")
                self.fail_pass[bootstrap_server] = 0
                continue
            for broker in brokers:
                if broker in self.producers:
                    producer = self.producers[broker]
                    self.producers.update(dict.fromkeys(brokers, producer))
                    self.producers[bootstrap_server] = producer
                    return producer
            try:
                producer = KafkaProducer(bootstrap_servers=brokers, **self.configs)
                self.producers.update(dict.fromkeys(brokers, producer))
                self.producers[bootstrap_server] = producer
                return producer
            except Exception as e:
                self.logger.warning(f"can not init producer {bootstrap_server} {e}")

    def close(self, timeout=None):
        for producer in self.producers.values():
            producer.flush(timeout)
            producer.close(timeout)
        self.producers = {}
