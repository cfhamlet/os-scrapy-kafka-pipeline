# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging
from typing import List, Optional, Tuple

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.utils.python import to_bytes

from .exporter import TextDictKeyPythonItemExporter
from .producer import AutoProducer
from .serialize import ScrapyJSNONBase64Encoder
from .utils import loglevel, max_str

KAFKA_PRODUCER_BROKERS = "KAFKA_PRODUCER_BROKERS"
KAFKA_PRODUCER_CONFIGS = "KAFKA_PRODUCER_CONFIGS"
KAFKA_PRODUCER_TOPIC = "KAFKA_PRODUCER_TOPIC"
KAFKA_PRODUCER_LOGLEVEL = "KAFKA_PRODUCER_LOGLEVEL"
KAFKA_PRODUCER_CLOSE_TIMEOUT = "KAFKA_PRODUCER_CLOSE_TIMEOUT"


class KafkaPipeline(object):
    def __init__(self, crawler):
        self.crawler = crawler
        settings = self.crawler.settings
        try:
            self.producer = AutoProducer(
                bootstrap_servers=settings.get(KAFKA_PRODUCER_BROKERS, None),
                configs=settings.get(KAFKA_PRODUCER_CONFIGS, None),
                topic=settings.get(KAFKA_PRODUCER_TOPIC, None),
                kafka_loglevel=loglevel(
                    settings.get(KAFKA_PRODUCER_LOGLEVEL, "WARNING")
                ),
            )
        except Exception as e:
            raise NotConfigured(f"init producer {e}")
        self.logger = logging.getLogger(self.__class__.__name__)
        crawler.signals.connect(self.spider_closed, signals.spider_closed)
        self.exporter = TextDictKeyPythonItemExporter(binary=False)
        self.encoder = ScrapyJSNONBase64Encoder()

    def kafka_args(
        self, item
    ) -> Tuple[
        Optional[str],  # topic
        Optional[bytes],  # key
        Optional[List[Tuple[str, bytes]]],  # headers
        Optional[int],  # partition
        Optional[int],  # timestamp_ms
        Optional[List[str]],
    ]:
        topic = key = headers = partition = timestamp_ms = bootstrap_servers = None
        if hasattr(item, "meta") and isinstance(item.meta, dict):
            meta = item.meta
            topic = meta.get("kafka.topic", None)
            key = meta.get("kafka.key", None)
            partition = meta.get("kafka.partition", None)
            bootstrap_servers = meta.get("kafka.brokers", None)
            if isinstance(bootstrap_servers, str):
                bootstrap_servers = bootstrap_servers.split(",")

        return topic, key, headers, partition, timestamp_ms, bootstrap_servers

    def kafka_value(self, item) -> Optional[bytes]:
        result = self.exporter.export_item(item)
        return to_bytes(self.encoder.encode(result))

    def process_item(self, item, spider):
        try:
            (
                topic,
                key,
                headers,
                partition,
                timestamp_ms,
                bootstrap_servers,
            ) = self.kafka_args(item)
            value = self.kafka_value(item)
            self.producer.send(
                topic=topic,
                value=value,
                key=key,
                headers=headers,
                partition=partition,
                timestamp_ms=timestamp_ms,
                bootstrap_servers=bootstrap_servers,
            )
        except Exception as e:
            show_me = max_str(str(item), 200)
            self.logger.error(f"process item {e} {show_me}")
        return item

    def spider_closed(self, spider):
        if self.producer is not None:
            settings = self.crawler.settings
            self.producer.close(settings.get(KAFKA_PRODUCER_CLOSE_TIMEOUT, None))
            self.producer = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
