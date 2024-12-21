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
```sql
select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at from langfarm.tracing.observations order by created_at desc limit 10;
```

结果如下：
```console
Flink SQL> select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at from langfarm.tracing.observations order by created_at desc limit 10;
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
|                             id |             name |                          input |                 created_at |                 updated_at |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
| 2a6f3018-ccff-4eb6-9461-290... | JsonOutputParser | ```json {   "a": "b + c" } ``` | 2024-12-21 16:41:10.121363 | 2024-12-21 16:41:10.121984 |
| 58b66f13-1e89-4d35-b94f-3d0... |           Tongyi | 把 a = b + c 转成 json 对象...   | 2024-12-21 16:41:09.385968 | 2024-12-21 16:41:10.120453 |
| 9c3727d6-56e4-414a-ba98-f22... | RunnableSequence | 把 a = b + c 转成 json 对象...   | 2024-12-21 16:41:09.385034 | 2024-12-21 16:41:10.122040 |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+
3 rows in set (1.01 seconds)
```