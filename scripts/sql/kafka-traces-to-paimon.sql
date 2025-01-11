-- kafka 的 traces 源表, 用临时表更方便。
CREATE TEMPORARY TABLE kafka_traces_source (
    id STRING NOT NULL,
    `timestamp` TIMESTAMP_LTZ,
    name STRING,
    project_id STRING,
    metadata STRING,
    external_id STRING,
    user_id STRING,
    `release` STRING,
    version STRING,
    public BOOLEAN,
    bookmarked BOOLEAN,
    input STRING,
    output STRING,
    session_id STRING,
    tags STRING,
    -- __pt_time__ 与 created_at 字段共用
    created_at TIMESTAMP_LTZ,
    updated_at TIMESTAMP_LTZ,
    __id__ STRING
)
WITH (
    'connector' = 'kafka',
    'topic' = 'traces',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'kafka-traces-to-paimon',
--    'scan.startup.mode' = 'group-offsets',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    -- 格式 "yyyy-MM-ddTHH:mm:ss.s{precision}Z"
    'json.timestamp-format.standard' = 'ISO-8601',
    'json.ignore-parse-errors' = 'true',
    'json.map-null-key.mode' = 'DROP',
    'json.encode.decimal-as-plain-number' = 'true'
)
;

-- 从源表复制表结构来创建目标表
CREATE TABLE IF NOT EXISTS langfarm.tracing.traces (
    -- 分区字段，按需要增加。
    dt STRING,
    hh STRING,
    PRIMARY KEY (dt, hh, id) NOT ENFORCED
--    PRIMARY KEY (id) NOT ENFORCED
)
-- 可以增加 天/小时 分区
PARTITIONED BY (dt, hh)
WITH (
    'merge-engine' = 'partial-update',
    'changelog-producer' = 'lookup',
    -- 分桶默认参数，按需改。
--    'bucket' = '-1',
--    'dynamic-bucket.target-row-num' = '2000000',
    -- 最小 bucket 数，可以增加并行任务。一个 bucket 一个并行。
    'dynamic-bucket.initial-buckets' = '4',
    'sink.watermark-time-zone' = 'GMT+08:00'
)
LIKE kafka_traces_source (
    -- 去除源表 options
    EXCLUDING OPTIONS
)
;

-- 写入到 paimon 的 traces 表
INSERT INTO langfarm.tracing.traces
SELECT
*
-- 更新也会 created_at 字段
,DATE_FORMAT(created_at, 'yyyy-MM-dd') AS dt
,DATE_FORMAT(created_at, 'HH') AS hh
FROM kafka_traces_source
;