兼容 Langfuse Tracing 的 Python 版本服务器。接到 tracing 数据转发到 kafka 中。kafka 可以再写到数据湖中。

## tracing 数据写到 paimon 示例：

步骤：
1、通过 langfarm-tracing 服务接到 langfuse sdk 上报的数据，再转发到 kafka 中。
2、通过 flink sql 把 kafka 的数据写到 paimon 数据湖中。
3、可以用其它兼容 paimon 数据的引擎查询数据，示例使用 flink sql 查询。

### 启动相关环境

启动 langfuse
```bash
sh bin/start-langfuse-docker-compose.sh
```

打开 langfuse（以 v2 版本） http://localhost:3000 ，创建组织 -> 创建项目 -> 生成 pk/sk （保存好，下面示例需要用到）。

启动 kafka 服务

包括组件：
* kafka - [Apache Kafka 和 Python 入门](https://developer.confluent.io/get-started/python/)
* [kafka-ui](https://github.com/provectus/kafka-ui) - [docker compose 示例](https://docs.kafka-ui.provectus.io/configuration/compose-examples)

运行启动脚本

```bash
sh bin/start-kafka-docker-compose.sh
```

本机增加 kafka 的 host 绑定：
```bash
# vi /etc/hosts
127.0.0.1 kafka
```

本地配置文件：
```bash
# 配置模板复制为 .env
cp .env.local.template .env

# 配置 kafka 地址
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

测试本地环境到 kafka 的连通性。
```bash
python -m unittest tests/test_kafka.py
```

查看 kafka 相关情况：http://localhost:8080/
* 查看刚刚测试运行的消息 http://localhost:8080/ui/clusters/langfarm/all-topics/events/messages

启动 flink + paimon 环境

构建 paimon-flink 镜像
```bash
# paimon、postgres-cdc、kafka 相关 lib；请看 docker/Dockerfile
# 增加 flink 的 checkpointing 和 catalog-store 配置，请看 docker/conf/config.yaml
sh bin/build-docker-paimon-flink.sh
```

启动 flink 和 paimon 环境
```bash
sh bin/start-paimon-flink-docker-compose.sh
```

进入 flink sql-client 的 docker
```bash
sh bin/run-flink-sql-client.sh
```

在进入的 flank-sql-client 的 docker 中执行。
```bash
# 进入后，初始化 langfarm 在 paimon 里需要的两个表：
# 确认是在 /opt/flink 目录
# cd /opt/flink
sh scripts/create-tables-in-paimon.sh

# 启动 traces 信息同步任务 kafka-traces-to-paimon
./bin/sql-client.sh -f scripts/sql/kafka-traces-to-paimon.sql
```

查看启动的 flink sql 任务 http://localhost:8081/#/job/running


### Langfarm Tracing 接 langfuse 上报日志

前提：
* 有 kafka 环境，langfarm-tracing 服务端 .env 配置：KAFKA_BOOTSTRAP_SERVERS。
* 有 flink + paimon 环境
* 有 langfuse 的 postgres，langfarm 使用 api_key 数据用于接口监权。
* 启动 langfarm-tracing 服务。

启动 langfarm-tracing 服务
```bash
sh run-server.sh
```

langfuse sdk 上报

使用 langfarm-tracing 来接 langfuse sdk 的 trace 上报

llm 应用改 LANGFUSE_HOST 配置，指向 langfarm-tracing 服务端的地址取可:
```dotenv
## 修改成本地测试环境的 langfuse pk/sk
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=http://localhost:8000
# tongyi API Key
DASHSCOPE_API_KEY=sk-xxx
```

上报 langfuse trace 示例：
```bash
python post_langfuse_traces_with_langfarm.py
```

### 查询 paimon 的数据

默认 checkpoint 时间是 3 分钟，即 3 分钟后，可以用 flink sql 查 paimon 的数据：
```bash
# 查 flink sql 中查询。
# 在刚才进行的 flink sql-client docker 中进入。
./bin/sql-client.sh
```

flink sql 查询 paimon 的数据：
```sql
-- use tableau result mode
SET 'sql-client.execution.result-mode' = 'tableau';

-- 用 '批模型' 运行查询数据
SET 'execution.runtime-mode' = 'batch';

-- 查询
select id, name, input, output, created_at, updated_at from langfarm.tracing.traces order by created_at desc limit 10;
```

结果如下：
```console
Flink SQL> select id, name, input, output, created_at, updated_at from langfarm.tracing.traces order by created_at desc limit 10;
+--------------------------------+------------------+--------------------------------+----------------+-------------------------+-------------------------+
|                             id |             name |                          input |         output |              created_at |              updated_at |
+--------------------------------+------------------+--------------------------------+----------------+-------------------------+-------------------------+
| 239ea345-03b9-4a0f-93aa-a33... | RunnableSequence | 把 a = b + c 转成 json 对象...   | {"a": "b + c"} | 2024-12-21 10:06:54.415 | 2024-12-21 10:06:54.932 |
+--------------------------------+------------------+--------------------------------+----------------+-------------------------+-------------------------+
1 row in set (0.60 seconds)
```

可以看下数据目录
```console
 % tree /tmp/langfarm-tracing/paimon/tracing.db/traces
/tmp/langfarm-tracing/paimon/tracing.db/traces
├── bucket-0
│   ├── changelog-3c2e21c7-8820-43ab-8cb8-da1731fc7a1a-0.parquet
│   └── data-0a5bd775-e382-4c83-af3e-18f29abd7154-0.parquet
├── index
│   └── index-93f6bda9-6f87-4a08-9347-559b7e78c1fb-0
├── manifest
│   ├── index-manifest-0c42ca83-c94c-41ca-873a-9ede81ab4c46-0
│   ├── manifest-7e357907-b597-44cd-b0f7-820553110d6b-0
│   ├── manifest-7e357907-b597-44cd-b0f7-820553110d6b-1
│   ├── manifest-7e357907-b597-44cd-b0f7-820553110d6b-2
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-0
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-1
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-2
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-3
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-4
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-5
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-6
│   ├── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-7
│   └── manifest-list-5f1647b2-ea32-4def-848e-36c895210e5a-8
├── schema
│   └── schema-0
└── snapshot
    ├── EARLIEST
    ├── LATEST
    ├── snapshot-1
    ├── snapshot-2
    ├── snapshot-3
    └── snapshot-4

6 directories, 23 files
```

