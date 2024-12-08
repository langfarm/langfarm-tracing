开发者相关说明

## 使用的技术
* Poetry - [Python 依赖构建管理工具](http://chenlb.com/python/advanced/poetry.html)
* FastAPI
* Postgresql
* SQLAlchemy
* Langfuse
* Docker - 用于搭建本地测试环境
* Kafka
* Flink

## 开发环境

使用 docker compose

### Langfuse 相关

### 实时流相关

包括组件：
* kafka - [Apache Kafka 和 Python 入门](https://developer.confluent.io/get-started/python/)
* [kafka-ui](https://github.com/provectus/kafka-ui) - [docker compose 示例](https://docs.kafka-ui.provectus.io/configuration/compose-examples)
* flink

运行启动脚本

```bash
sh scripts/start-docker-compose-bigdata.sh
```

本机增加 kafka 的 host 绑定：
```bash
# vi /etc/hosts
127.0.0.1 kafka0
```

本地配置文件：
```bash
# 配置模板复制为 .env
cp .env.local.template .env

# 配置 kafka 地址
kafka_bootstrap_servers=kafka0:29092
```

测试本地环境到 kafka 的连通性。
```bash
python -m unittest tests/test_kafka.py
```

查看 kafka 相关情况：http://localhost:8080/
* 查看刚刚测试运行的消息 http://localhost:8080/ui/clusters/langfarm/all-topics/events/messages
