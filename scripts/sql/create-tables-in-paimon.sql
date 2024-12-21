CREATE TABLE IF NOT EXISTS langfarm.tracing.traces (
    id STRING,
    `timestamp` TIMESTAMP_LTZ(3),
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
    created_at TIMESTAMP_LTZ(3),
    updated_at TIMESTAMP_LTZ(3),
--    dt STRING,
    PRIMARY KEY (id) NOT ENFORCED
)
--PARTITIONED BY (dt)
WITH (
    'merge-engine' = 'partial-update',
    'changelog-producer' = 'lookup',
    'sink.watermark-time-zone' = 'GMT+08:00'
--    'partition.timestamp-formatter' = 'yyyy-MM-dd',
--    'partition.timestamp-pattern' = '$dt',
--    'partition.time-interval' = '1 d',
--    'partition.idle-time-to-done' = '15 m',
--    'partition.mark-done-action' = 'done-partition',
--    'partition.expiration-time' = '1098 d',
--    'partition.expiration-check-interval' = '1 d'
)
;