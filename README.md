# scrapy_kafka_pipeline

该项目通过 pipeline 方式将 scrapy 框架中的 item 以 json 格式发送到 kafka。

特性：

* 支持 settings.py 中配置默认 kafka brokers 以及 topic 
* 支持为 [kafka-python](https://github.com/dpkp/kafka-python) [producer](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html) 配置初始化参数
* 支持根据 item 增加额外信息动态增加目标 kafka 集群以及 topic
* item 转换成为 JSON 格式发送到 kafka， item 中的 bytes 类型数据编码为 base64


## Install

```
python setup.py install
```

若已经安装 Scrapy 框架，则在项目根路径下可直接运行 demo

```
scrapy crawl demo
```

## Usage


### 配置项

* 启用 pipeline，在 settings.py 文件中配置即可

    ```
    ITEM_PIPELINES = {
        "scrapy_kafka_pipeline.KafkaPipeline": 300,
    }
    ```

* 配置默认 kafka brokers

    ```
    KAFKA_PRODUCER_BROKERS = ["broker01.kafka:9092", "broker02.kafka:9092"]
    ```

    - item 中指定的 brokers 地址覆盖该配置项
    - 若配置错误，无法建立 kafka 连接，则该 pipeline 启用失败
    - 若未配置该项且 item 中未指定 brokers 地址，则发送 item 时报错

* 配置默认 kafka producer [参数](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html)

    ```
    KAFKA_PRODUCER_CONFIGS = {"client_id": "id01", "retries": 1}
    ```

    - 该配置为全局配置，动态连接的 producer 也使用该配置初始化
    - 若已经通过 ``KAFKA_PRODUCER_BROKERS`` 配置了 brokers，则该配置中的 ``bootstrap_servers`` 不生效

* 配置默认 topic

    ```
    KAFKA_PRODUCER_TOPIC = "topic01"
    ```

    - item 中指定的 topic 覆盖该配置项
    - 若未配置该项且 item 中未指定 topic，则发送 item 时报错

* 配置 kafka-python loglevel (默认 "WARNING")

    ```
    KAFKA_PRODUCER_LOGLEVEL = "DEBUG"
    ```

* 配置在scrapy进程退出时关闭 kafka producer 等待秒数 (默认 None)

    ```
    KAFKA_PRODUCER_CLOSE_TIMEOUT = 10
    ```

### item 中指定参数

* 在 item 中可以指定其他 kafka 集群的 brokers 地址，topic，key，partition
* item 需有名为 meta 成员，类型为 dict
* 可选配置项：

    ```
    meta = {
        "kafka.topic": "topic01",
        "kafka.key": "key01",
        "kafka.partition": 1,
        "kafka.brokers": "broker01.kafka:9092,broker02.kafka:9092"
    }
    ```

### 存储格式

item 序列化为 JSON 格式，item 中的 bytes 类型数据会以 base64 编码

## Unit Tests

```
sh scripts/test.sh
```

## License

MIT licensed.