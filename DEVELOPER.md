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
select id,SPLIT_INDEX(id, '-', 5) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 10;
```

结果如下：
```console
Flink SQL> select id,SPLIT_INDEX(id, '-', 5) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 10;
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
|                             id |        sid |             name |                          input |                 created_at |                 updated_at |         dt | hh |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
| b7ee6e3a-bf46-4b86-8dd1-778... | 2024122123 | JsonOutputParser | ```json {   "a": "b + c" } ``` | 2024-12-21 23:35:43.534559 | 2024-12-21 23:35:43.536412 | 2024-12-21 | 23 |
| cc8c5fa7-4b2f-4f8e-a612-8aa... | 2024122123 |           Tongyi | 把 a = b + c 转成 json 对象...   | 2024-12-21 23:34:27.653988 | 2024-12-21 23:35:43.531273 | 2024-12-21 | 23 |
| 3657c645-e6c5-49fa-8abd-9bb... | 2024122123 | RunnableSequence | 把 a = b + c 转成 json 对象...   | 2024-12-21 23:34:27.653030 | 2024-12-21 23:35:43.536515 | 2024-12-21 | 23 |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
4 rows in set (0.77 seconds)
```

目录结构：
```console
% tree /tmp/langfarm-tracing/paimon/tracing.db/observations 
/tmp/langfarm-tracing/paimon/tracing.db/observations
├── dt=2024-12-21
│   └── hh=23
│       └── bucket-0
│           ├── changelog-da44ce5c-642f-4fed-9cea-cd5da8511162-0.parquet
│           └── data-fea89864-80d7-40c5-be90-c7a4cbc4745b-0.parquet
├── index
│   └── index-8c6eac9f-96db-49c7-b8a4-08224bc07a42-0
├── manifest
│   ├── index-manifest-8678f8f9-8de5-4d48-8e3d-85bd92f7f59d-0
│   ├── manifest-cdeb3a13-5061-4e73-ad42-302f4794f3b4-0
│   ├── manifest-cdeb3a13-5061-4e73-ad42-302f4794f3b4-1
│   ├── manifest-cdeb3a13-5061-4e73-ad42-302f4794f3b4-2
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-0
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-1
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-2
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-3
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-4
│   ├── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-5
│   └── manifest-list-4a1f10d5-0a1f-4ae1-b4d9-2af4970e06ae-6
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