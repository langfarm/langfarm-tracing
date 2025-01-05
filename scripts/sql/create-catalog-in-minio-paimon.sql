CREATE CATALOG IF NOT EXISTS langfarm WITH (
    'type' = 'paimon',
    'warehouse' = 's3://paimon/langfarm',
    's3.endpoint' = 'http://minio:9000',
    's3.access-key' = 'AAAAAAAAAAAAAAAAAAAA',
    's3.secret-key' = 'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
    's3.path.style.access' = 'true'
);

-- 可能 flink sql 有 bug：langfarm.yaml 的内容为 s3.path.style.access: "'true'" 了，不能在这个 catalog 下操作。
-- 需要改下 /tmp/langfarm-tracing/catalog/langfarm.yaml 文件。
-- 把 s3.path.style.access: "'true'" 改为 s3.path.style.access: "true" 或 s3.path.style.access: true
