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

启动 kafka-to-paimon 任务
在进入的 flank-sql-client 的 docker 中执行。
```bash
# 进入后，初始化 langfarm 在 paimon 里需要的两个表：
# 确认是在 /opt/flink 目录
# cd /opt/flink

# 启动 traces/observations 信息同步任务
sh scripts/kafka-traces-to-paimon.sh
sh scripts/kafka-observations-to-paimon.sh
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

-- 查询 observations 表
-- select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at from langfarm.tracing.observations order by created_at desc limit 10;
```

traces 结果如下：
```console
Flink SQL> select id, name, input, created_at, updated_at from langfarm.tracing.traces order by created_at desc limit 10;
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
|                             id |             name |                          input |                 created_at |                 updated_at |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
| afb48fbd-70f3-40e8-9f8b-392... | RunnableSequence | 把 a = b + c 转成 json 对象...   | 2024-12-21 16:41:09.384950 | 2024-12-21 16:41:10.122093 |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
1 row in set (0.64 seconds)
```

可以看下数据目录
```console
 % tree /tmp/langfarm-tracing/paimon/tracing.db/traces
/tmp/langfarm-tracing/paimon/tracing.db/traces
├── bucket-0
│   ├── changelog-42238d2f-9501-4220-8634-943e0a79f082-0.parquet
│   └── data-afbc14c2-abc0-4720-b0cf-122d1a66163a-0.parquet
├── index
│   └── index-d7dd71b7-ffb8-4e15-b4f5-b601291bda9e-0
├── manifest
│   ├── index-manifest-0906d795-98d9-40c0-8e2e-5fe1d7d386b6-0
│   ├── manifest-85c77495-1a93-4c5c-8a36-6eea7594e9cf-0
│   ├── manifest-85c77495-1a93-4c5c-8a36-6eea7594e9cf-1
│   ├── manifest-85c77495-1a93-4c5c-8a36-6eea7594e9cf-2
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-0
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-1
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-2
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-3
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-4
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-5
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-6
│   ├── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-7
│   └── manifest-list-f84372e5-2524-40a7-a54a-a10f77e738f9-8
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

