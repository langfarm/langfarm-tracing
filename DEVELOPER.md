开发者相关说明

## 使用的技术
* Poetry - [Python 依赖构建管理工具](http://chenlb.com/python/advanced/poetry.html)
* FastAPI
* Postgresql
* SQLAlchemy
* Langfuse
* Kafka
* Flink
* Docker - 用于搭建本地测试环境

## 开发环境

使用 docker compose

见 README 的示例部分。

observations 表
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

# 启动 observations 信息同步任务 kafka-observations-to-paimon
./bin/sql-client.sh -f scripts/sql/kafka-observations-to-paimon.sql
```

```console
Flink SQL> select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, REGEXP_REPLACE(output, '\n', ' ') as output, created_at, updated_at from langfarm.tracing.observations order by created_at desc limi
t 10;
+--------------------------------+------------------+--------------------------------+--------------------------------+-------------------------+-------------------------+
|                             id |             name |                          input |                         output |              created_at |              updated_at |
+--------------------------------+------------------+--------------------------------+--------------------------------+-------------------------+-------------------------+
| dc66f2d5-4317-4f40-a9f6-2c6... | JsonOutputParser | ```json {   "a": "b + c" } ``` |                 {"a": "b + c"} | 2024-12-21 10:06:54.931 | 2024-12-21 10:06:54.931 |
| 3f7cd303-529e-40b6-a4ef-7e3... | RunnableSequence | 把 a = b + c 转成 json 对象...   |                 {"a": "b + c"} | 2024-12-21 10:06:54.416 | 2024-12-21 10:06:54.931 |
| c21f2156-6cc0-45c1-85e8-d10... |           Tongyi | 把 a = b + c 转成 json 对象...   | ```json {   "a": "b + c" } ``` | 2024-12-21 10:06:54.416 | 2024-12-21 10:06:54.930 |
+--------------------------------+------------------+--------------------------------+--------------------------------+-------------------------+-------------------------+
3 rows in set (0.76 seconds)
```