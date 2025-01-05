开发者相关说明

## 版本号

按 [语义化版本](https://semver.org/lang/zh-CN/) 标准。

版本格式：主版本号.次版本号.修订号 （MAJOR.MINOR.PATCH），版本号递增规则如下：

* MAJOR - 主版本号：当你做了不兼容的 API 修改，
* MINOR - 次版本号：当你做了向下兼容的功能性新增，
* PATCH - 修订号：当你做了向下兼容的问题修正。

## commit 规范

提交约定：[Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/)

* **fix**: 类型 为 fix 的提交表示在代码库中修复了一个 bug（这和语义化版本中的 ```PATCH``` 相对应）。
* **feat**: 类型 为 feat 的提交表示在代码库中新增了一个功能（这和语义化版本中的 ```MINOR``` 相对应）。
* **BREAKING CHANGE**: 在脚注中包含 BREAKING CHANGE: 或 <类型>(范围) 后面有一个 ! 的提交，表示引入了破坏性 API 变更（这和语义化版本中的 ```MAJOR``` 相对应）。 破坏性变更可以是任意 类型 提交的一部分。
* 其它：
  * build: 用于修改项目构建系统，例如修改依赖库、外部接口或者升级 Node 版本等；
  * chore: 用于对非业务性代码进行修改，例如修改构建流程或者工具配置等；
  * ci: 用于修改持续集成流程，例如修改 Travis、Jenkins 等工作流配置；
  * docs: 用于修改文档，例如修改 README 文件、API 文档等；
  * style: 用于修改代码的样式，例如调整缩进、空格、空行等；
  * refactor: 用于重构代码，例如修改代码结构、变量名、函数名等但不修改功能逻辑；
  * perf: 用于优化性能，例如提升代码的性能、减少内存占用等；
  * test: 用于修改测试用例，例如添加、删除、修改代码的测试用例等。
* 脚注中除了 ```BREAKING CHANGE: <description>``` ，其它条目应该采用类似 git trailer format 这样的惯例。

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
select id,SPLIT_INDEX(id, '-', 4) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 10;
```

结果如下：
```console
Flink SQL> select id,SPLIT_INDEX(id, '-', 4) as sid, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by created_at desc limit 10;
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
|                             id |        sid |             name |                          input |                 created_at |                 updated_at |         dt | hh |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
| 11e675a5-e0f3-461d-b315-173... | 1736068751 | JsonOutputParser | ```json {   "a": "b + c" } ``` | 2025-01-05 17:19:12.043923 | 2025-01-05 17:19:12.044509 | 2025-01-05 | 17 |
| 4b1ec263-ddf3-4285-9ee1-173... | 1736068751 |           Tongyi | 把 a = b + c 转成 json 对象... | 2025-01-05 17:19:11.146384 | 2025-01-05 17:19:12.043097 | 2025-01-05 | 17 |
| a7dbc3c0-cf9e-47b3-bd18-173... | 1736068751 | RunnableSequence | 把 a = b + c 转成 json 对象... | 2025-01-05 17:19:11.144777 | 2025-01-05 17:19:12.044572 | 2025-01-05 | 17 |
+--------------------------------+------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
3 rows in set (0.74 seconds)
```

目录结构：
```console
% tree /tmp/langfarm-tracing/paimon/langfarm/tracing.db/observations
/tmp/langfarm-tracing/paimon/langfarm/tracing.db/observations
├── dt=2025-01-05
│   └── hh=17
│       └── bucket-0
│           ├── changelog-da2c2f92-55bd-49cc-b4ef-c715b42cc25b-0.parquet
│           └── data-7ad4eca0-9068-4af8-b23a-a25cd344a1e2-0.parquet
├── index
│   └── index-aceed76f-2c58-42ed-9f98-6f2039cfce08-0
├── manifest
│   ├── index-manifest-2ebf74e4-69b8-4eac-8215-785addf76837-0
│   ├── manifest-2cb055fc-7c65-490e-a085-f41891bbf65f-0
│   ├── manifest-2cb055fc-7c65-490e-a085-f41891bbf65f-1
│   ├── manifest-2cb055fc-7c65-490e-a085-f41891bbf65f-2
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-0
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-1
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-2
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-3
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-4
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-5
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-6
│   ├── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-7
│   └── manifest-list-f23b7f63-9385-4ccb-897a-415952e5a660-8
├── schema
│   └── schema-0
└── snapshot
    ├── EARLIEST
    ├── LATEST
    ├── snapshot-1
    ├── snapshot-2
    ├── snapshot-3
    └── snapshot-4

8 directories, 23 files
```