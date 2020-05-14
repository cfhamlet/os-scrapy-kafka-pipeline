# os-scrapy-kafka-pipeline

[![Build Status](https://www.travis-ci.org/cfhamlet/os-scrapy-kafka-pipeline.svg?branch=master)](https://www.travis-ci.org/cfhamlet/os-scrapy-kafka-pipeline)
[![codecov](https://codecov.io/gh/cfhamlet/os-scrapy-kafka-pipeline/branch/master/graph/badge.svg)](https://codecov.io/gh/cfhamlet/os-scrapy-kafka-pipeline)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/os-scrapy-kafka-pipeline.svg)](https://pypi.python.org/pypi/os-scrapy-kafka-pipeline)
[![PyPI](https://img.shields.io/pypi/v/os-scrapy-kafka-pipeline.svg)](https://pypi.python.org/pypi/os-scrapy-kafka-pipeline)


This project provide pipeline to send Scrapy Item to kafka as JSON format

Features:

* support config default kafka brokers and topic in the settings.py file
* support [kafka-python](https://github.com/dpkp/kafka-python) [producer](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html) init args
* support dynamic connect and send to other kafka cluster and topic using item meta
* item will send to kafka as JSON format, bytes can be encoded to base64 string if it can not be utf-8 encoded

## Install

```
pip install os-scrapy-kafka-pipeline
```

You can run example spider directly in the project root path.

```
scrapy crawl example
```

## Usage


### Settings

* enable pipeline in the project settings.py file

    ```
    ITEM_PIPELINES = {
        "os_scrapy_kafka_pipeline.KafkaPipeline": 300,
    }
    ```

* config default kafka brokers

    ```
    KAFKA_PRODUCER_BROKERS = ["broker01.kafka:9092", "broker02.kafka:9092"]
    ```

    - brokers in the item meta will override this default value
    - pipeline will not be enabled when this settings can not to start kafka connection
    - it will raise exception when no brokers configured

* config default kafka [producer](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html)

    ```
    KAFKA_PRODUCER_CONFIGS = {"client_id": "id01", "retries": 1}
    ```

    - this is global config, the dynamic connections will use this configs
    - the ``bootstrap_servers`` will not work when ``KAFKA_PRRDUCER_BROKERS`` already configured

* config defult topic

    ```
    KAFKA_PRODUCER_TOPIC = "topic01"
    ```

    - the config in the item.meta will override this config
    - it will raise exception when no topic configured

* config kafka-python loglevel (default "WARNING")

    ```
    KAFKA_PRODUCER_LOGLEVEL = "DEBUG"
    ```

* config kafka producer close timeout (default: None)

    ```
    KAFKA_PRODUCER_CLOSE_TIMEOUT = 10
    ```

* ensure base64

    the bytes type of the item mumber will be encoded by utf-8, if encode fail, the pipeline can use base64 encode the bytes when you set:


    ```
    ENSURE_BASE64 = True
    ```

### Dynamic Kafka Connection with item.meta

* you can set topic, key, partition using item.meta
* the item must has meta mumber which type is dict
* options:

    ```
    meta = {
        "kafka.topic": "topic01",
        "kafka.key": "key01",
        "kafka.partition": 1,
        "kafka.brokers": "broker01.kafka:9092,broker02.kafka:9092"
    }
    ```

### Storage Format

Item will send to kafka as JSON format, bytes will encode to base64

## Unit Tests

```
sh scripts/test.sh
```

## License

MIT licensed.
