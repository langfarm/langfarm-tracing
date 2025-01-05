
## 用 sql 创建在 minio 中的 paimon catalog

```sql
-- ./bin/sql-client.sh 命令来进入 Flink SQL 客户端。
-- 如之前的示例数据是保存在本机 /tmp/langfarm-tracing/paimon/langfarm 目录里
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

需要本机改下 /tmp/langfarm-tracing/catalog-store/langfarm.yaml 文件。

把 s3.path.style.access: ```"'true'"``` 改为 s3.path.style.access: ```"true"``` 或 s3.path.style.access: ```true```。
内容如下（也可以省去 SQL 创建 catalog 的步骤，直接在本机修改 /tmp/langfarm-tracing/catalog-store/langfarm.yaml 的内容如下）：

```yaml
s3.access-key: "AAAAAAAAAAAAAAAAAAAA"
s3.secret-key: "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
s3.endpoint: "http://minio:9000"
type: "paimon"
warehouse: "s3://paimon/langfarm"
s3.path.style.access: true
```