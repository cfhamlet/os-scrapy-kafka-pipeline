# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging
import time
from functools import partial
from typing import List, Optional, Tuple

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.utils.python import to_bytes
from twisted.internet import threads

from .exporter import TextDictKeyPythonItemExporter
from .producer import AutoProducer
from .serialize import ScrapyJSNONBase64Encoder
from .utils import loglevel

KAFKA_PRODUCER_BROKERS = "KAFKA_PRODUCER_BROKERS"
KAFKA_PRODUCER_CONFIGS = "KAFKA_PRODUCER_CONFIGS"
KAFKA_PRODUCER_TOPIC = "KAFKA_PRODUCER_TOPIC"
KAFKA_PRODUCER_LOGLEVEL = "KAFKA_PRODUCER_LOGLEVEL"
KAFKA_PRODUCER_CLOSE_TIMEOUT = "KAFKA_PRODUCER_CLOSE_TIMEOUT"
KAFKA_VALUE_ENSURE_BASE64 = "KAFKA_VALUE_ENSURE_BASE64"


def round5(n):
    return round(n, 5)


class KafKaRecord(object):
    __slots__ = (
        "topic",
        "value",
        "key",
        "headers",
        "partition",
        "timestamp_ms",
        "bootstrap_servers",
        "meta",
        "ts",
        "dmsg",
    )

    def __init__(self):
        self.topic: Optional[str] = None
        self.value: Optional[bytes] = None
        self.key: Optional[bytes] = None
        self.headers: Optional[List[Tuple[str, bytes]]] = None
        self.partition: Optional[int] = None
        self.timestamp_ms: Optional[int] = None
        self.bootstrap_servers: Optional[List[str]] = None
        self.meta: Optional[dict] = None
        self.ts: int = 0
        self.dmsg: dict = {}


class KafkaPipeline(object):
    def __init__(self, crawler):
        self.crawler = crawler
        settings = self.crawler.settings
        try:
            self.producer = AutoProducer(
                bootstrap_servers=settings.getlist(KAFKA_PRODUCER_BROKERS),
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
        self.exporter = TextDictKeyPythonItemExporter(
            binary=False,
            ensure_base64=settings.getbool(KAFKA_VALUE_ENSURE_BASE64, False),
        )
        self.encoder = ScrapyJSNONBase64Encoder()
        self.field_filter = set(settings.getlist("KAFKA_EXPORT_FILTER", []))
        self.logger.debug(f"KAFKA_EXPORT_FILTER: {self.field_filter}")

    def kafka_record(self, item) -> KafKaRecord:
        record = KafKaRecord()
        if "meta" in item and isinstance(item["meta"], dict):
            meta = item["meta"]
            record.meta = meta
            record.topic = meta.get("kafka.topic", None)
            record.key = meta.get("kafka.key", None)
            record.partition = meta.get("kafka.partition", None)
            bootstrap_servers = meta.get("kafka.brokers", None)
            if isinstance(bootstrap_servers, str):
                record.bootstrap_servers = bootstrap_servers.split(",")

        return record

    def kafka_value(self, item, record) -> Optional[bytes]:
        record.ts = time.time()
        try:
            result = self.exporter.export_item(
                item, pre="", field_filter=self.field_filter
            )
            record.value = to_bytes(self.encoder.encode(result))
            record.dmsg["size"] = len(record.value)
        except Exception as e:
            record.dmsg["err"] = e
            raise e
        finally:
            record.dmsg["encode_cost"] = round5(time.time() - record.ts)

    def _log_msg(self, item, record):
        err = record.dmsg.pop("err", None)
        msg = " ".join(
            [
                f"{k}:{v:.5f}" if k.endswith("_cost") else f"{k}:{v}"
                for k, v in record.dmsg.items()
            ]
        )
        msg = f"topic:{record.topic} partition:{record.partition} {msg}"
        if err:
            self.logger.error
            msg = f"{msg} err:{err}"
            record.dmsg["err"] = err
        return msg

    def log(self, item, record):
        logf = self.logger.debug
        if "err" in record.dmsg and record.dmsg["err"]:
            logf = self.logger.error
        logf(self._log_msg(item, record))

    def on_send_succ(self, item, record, metadata):
        record.topic = metadata.topic
        record.partition = metadata.partition
        record.dmsg["offset"] = metadata.offset
        record.dmsg["send_cost"] = round5(time.time() - record.ts)
        self.log(item, record)

    def on_send_fail(self, item, record, e):
        record.dmsg["err"] = e
        record.dmsg["send_cost"] = round5(time.time() - record.ts)
        self.log(item, record)

    def send(self, item, record):
        record.ts = time.time()
        if record.topic is None:
            record.topic = self.producer.topic
        try:
            self.producer.send(
                topic=record.topic,
                value=record.value,
                key=record.key,
                headers=record.headers,
                partition=record.partition,
                timestamp_ms=record.timestamp_ms,
                bootstrap_servers=record.bootstrap_servers,
            ).add_callback(partial(self.on_send_succ, item, record)).add_errback(
                partial(self.on_send_fail, item, record)
            )
        except Exception as e:
            record.dmsg["err"] = e
            record.dmsg["send_cost"] = round5(time.time() - record.ts)
            self.log(item, record)
        return item

    def process_item(self, item, spider):
        record = self.kafka_record(item)
        try:
            self.kafka_value(item, record)
        except:
            self.log(item, record)
            return item
        return threads.deferToThread(self.send, item, record)

    def spider_closed(self, spider):
        if self.producer is not None:
            settings = self.crawler.settings
            self.producer.close(settings.get(KAFKA_PRODUCER_CLOSE_TIMEOUT, None))
            self.producer = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
