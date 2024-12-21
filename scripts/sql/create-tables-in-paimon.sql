CREATE TABLE IF NOT EXISTS langfarm.tracing.traces (
    id STRING,
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
    created_at TIMESTAMP_LTZ,
    updated_at TIMESTAMP_LTZ,
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

CREATE TABLE IF NOT EXISTS langfarm.tracing.observations (
    id STRING,
    name STRING,
    start_time TIMESTAMP_LTZ,
    end_time TIMESTAMP_LTZ,
    parent_observation_id STRING,
    type STRING,
    trace_id STRING,
    metadata STRING,
    `model` STRING,
    modelParameters STRING,
    input STRING,
    output STRING,
    level STRING,
    status_message STRING,
    completion_start_time TIMESTAMP_LTZ,
    completion_tokens INT,
    prompt_tokens INT,
    total_tokens INT,
    version STRING,
    project_id STRING,
    created_at TIMESTAMP_LTZ,
    unit STRING,
    prompt_id STRING,
    input_cost numeric(65,30),
    output_cost numeric(65,30),
    total_cost numeric(65,30),
    internal_model STRING,
    updated_at TIMESTAMP_LTZ(3),
    calculated_input_cost numeric(65,30),
    calculated_output_cost numeric(65,30),
    calculated_total_cost numeric(65,30),
    internal_model_id STRING,
--    dt STRING,
    PRIMARY KEY (id) NOT ENFORCED
)
WITH (
    'merge-engine' = 'partial-update',
    'changelog-producer' = 'lookup',
    'sink.watermark-time-zone' = 'GMT+08:00'
)
;