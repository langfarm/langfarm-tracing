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
select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by updated_at desc limit 10;
```

结果如下：
```console
Flink SQL> select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at, dt, hh from langfarm.tracing.observations order by updated_at desc limit 10;
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
|                             id |             name |                          input |                 created_at |                 updated_at |         dt | hh |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
| d9f625e0-cfc2-41ef-a567-0ac... | RunnableSequence | 把 a = b + c 转成 json 对象... | 2025-01-11 10:22:05.916720 | 2025-01-11 10:22:06.720550 | 2025-01-11 | 10 |
| d9f625e0-cfc2-41ef-a6e0-536... | JsonOutputParser | ```json {   "a": "b + c" } ``` | 2025-01-11 10:22:05.916720 | 2025-01-11 10:22:06.720438 | 2025-01-11 | 10 |
| d9f625e0-cfc2-41ef-a154-498... |           Tongyi | 把 a = b + c 转成 json 对象... | 2025-01-11 10:22:05.916720 | 2025-01-11 10:22:06.717373 | 2025-01-11 | 10 |
+--------------------------------+------------------+--------------------------------+----------------------------+----------------------------+------------+----+
3 rows in set (0.85 seconds)

```

目录结构：
```console
% tree /tmp/langfarm-tracing/paimon/langfarm/tracing.db/observations
/tmp/langfarm-tracing/paimon/langfarm/tracing.db/observations
├── dt=2025-01-11
│   └── hh=10
│       └── bucket-0
│           ├── changelog-a7381c72-f2b4-4a0e-b0e8-b9605d7367b9-0.parquet
│           └── data-1265cb38-98e1-4e87-886c-c6d89c16feca-0.parquet
├── index
│   └── index-fbdc0c8e-e1b2-4dc5-bec2-417b94682313-0
├── manifest
│   ├── index-manifest-70921707-31c8-4fba-8c11-0ab5ffeaa7eb-0
│   ├── manifest-c1023420-950c-417b-8217-ac2db9e8e5c7-0
│   ├── manifest-c1023420-950c-417b-8217-ac2db9e8e5c7-1
│   ├── manifest-c1023420-950c-417b-8217-ac2db9e8e5c7-2
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-0
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-1
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-2
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-3
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-4
│   ├── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-5
│   └── manifest-list-dc244dfc-1cee-4695-949f-27f73cfbdddd-6
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