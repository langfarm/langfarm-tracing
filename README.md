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
select id,SPLIT_INDEX(id, '-', 5) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.traces order by created_at desc limit 10;

-- 查询 observations 表
-- select id,SPLIT_INDEX(id, '-', 5) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 10;
```

traces 结果如下：
```console
Flink SQL> select id,SPLIT_INDEX(id, '-', 5) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.traces order by created_at desc limit 10;
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
|                             id |        sid |             name |                          input |                 created_at |                 updated_at |         dt | hh |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
| f3d6e324-ca35-4677-9de4-032... | 2024122123 | RunnableSequence | 把 a = b + c 转成 json 对象...   | 2024-12-21 23:34:27.652947 | 2024-12-21 23:35:43.536616 | 2024-12-21 | 23 |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
2 rows in set (0.81 seconds)

```

可以看下数据目录
```console
% tree /tmp/langfarm-tracing/paimon/tracing.db/traces
/tmp/langfarm-tracing/paimon/tracing.db/traces
├── dt=2024-12-21
│   └── hh=23
│       └── bucket-0
│           ├── changelog-e9b7388e-f868-4337-b126-4137ec6c88dd-0.parquet
│           └── data-3020179e-e5a0-4b60-b958-fac4d104049c-0.parquet
├── index
│   └── index-eb68fb9f-8a11-4e8a-b1ed-204f471e3c34-0
├── manifest
│   ├── index-manifest-d11f9b05-2c7e-4ffb-89db-847d3a291d86-0
│   ├── manifest-8cb7aeee-a87d-4e56-8e2b-46ce153b4cf3-0
│   ├── manifest-8cb7aeee-a87d-4e56-8e2b-46ce153b4cf3-1
│   ├── manifest-8cb7aeee-a87d-4e56-8e2b-46ce153b4cf3-2
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-0
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-1
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-2
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-3
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-4
│   ├── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-5
│   └── manifest-list-dc092b4c-f295-481e-9b52-4fb7d1c1d374-6
├── schema
│   └── schema-0
└── snapshot
    ├── EARLIEST
    ├── LATEST
    ├── snapshot-1
    ├── snapshot-2
    └── snapshot-3

8 directories, 20 files
```

## 数据写 paimon + minio，使用 StarRocks 读取示例：

### 搭建 minio 和 StarRocks 环境

```bash
# 启动 minio 和 StarRocks 的 docker 环境
sh bin/start-starrocks-docker-compose.sh

# 有个 minio_mc 启动后，执行分配 ak 后自动停止，是正常情况。 
```

使用 ```miniouser``` 和 ```miniopassword``` 登录 minio：http://localhost:9001/ 。
* 创建 bucket：```paimon```
* 创建目录 ```langfarm```

### 创建 paimon 的 minio 的 catalog

可以先取消上面示例的两个 flink 任务。进入 http://localhost:8081/#/job/running JOB 取消（取消不会保存消息的位点，下面重新启动会从最早的数据消费。）

进入 flink sql-client 的 docker
```bash
sh bin/run-flink-sql-client.sh
```

创建 paimon catalog 保存数据到 minio
```sql
-- ./bin/sql-client.sh 命令来进入 Flink SQL 客户端。
-- 上面的示例数据是保存在本机 /tmp/langfarm-tracing/paimon 目录里
-- 可以先 drop 掉原来的 catalog，删除 catalog 不会删除数据。
-- DROP CATALOG langfarm
-- 重新创建 catalog，数据保存在 minio 中。
CREATE CATALOG langfarm WITH (
    'type' = 'paimon',
    'warehouse' = 's3://paimon/langfarm',
    's3.endpoint' = 'http://minio:9000',
    's3.access-key' = 'AAAAAAAAAAAAAAAAAAAA',
    's3.secret-key' = 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
    's3.path.style.access' = 'true'
);
```

可能 flink sql 有 bug：langfarm.yaml 的内容为 s3.path.style.access: "'true'" 了，不能在这个 catalog 下操作。

需要本机改下 /tmp/langfarm-tracing/catalog/langfarm.yaml 文件。

把 s3.path.style.access: ```"'true'"``` 改为 s3.path.style.access: ```"true"``` 或 s3.path.style.access: ```true```。
内容如下（也可以省去 SQL 创建 catalog 的步骤，直接在本机修改 /tmp/langfarm-tracing/catalog/langfarm.yaml 的内容如下）：

```yaml
s3.access-key: "AAAAAAAAAAAAAAAAAAAA"
s3.secret-key: "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
s3.endpoint: "http://minio:9000"
type: "paimon"
warehouse: "s3://paimon/langfarm"
s3.path.style.access: true
```

重新启动两个 flink 任务
```bash
# 启动 traces/observations 信息同步任务
sh scripts/kafka-traces-to-paimon.sh
sh scripts/kafka-observations-to-paimon.sh
```

3 分钟后，可以用上面两个 flink sql 查表的示例，验证两个表是否有数据。没有数据，可以运行 ```post_langfuse_traces_with_langfarm.py``` 再生成一次。

### 使用 StarRocks 查询

参考：[StarRocks Paimon Catalog](https://docs.starrocks.io/zh/docs/data_source/catalog/paimon_catalog/#%E5%85%BC%E5%AE%B9-s3-%E5%8D%8F%E8%AE%AE%E7%9A%84%E5%AF%B9%E8%B1%A1%E5%AD%98%E5%82%A8-1)

创建 StarRocks 的外部 catalog，在 starrocks-fe docker 内运行(或本地的 mysql cli 或 MySQL Workbench)
```bash
mysql -P 9030 -h 127.0.0.1 -u root --prompt="StarRocks > "
```

使用如下 SQL 创建 StarRocks catalog
```sql
CREATE EXTERNAL CATALOG langfarm
PROPERTIES
(
    "type" = "paimon",
    "paimon.catalog.type" = "filesystem",
    "paimon.catalog.warehouse" = "s3://paimon/langfarm",
    "aws.s3.enable_path_style_access" = "true",
    "aws.s3.endpoint" = "http://minio:9000",
    "aws.s3.access_key" = "AAAAAAAAAAAAAAAAAAAA",
    "aws.s3.secret_key" = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
);
```

mysql 客户端查数据
```sql
select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.traces order by created_at desc limit 0, 10;

select id, name, input, trace_id, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 0, 10;
```
