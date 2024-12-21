
CREATE TEMPORARY TABLE kafka_traces_source (
    id STRING,
    `timestamp` TIMESTAMP(6),
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
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6)
)
WITH (
  'connector' = 'kafka',
  'topic' = 'traces',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'kafka-traces-to-paimon',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  'json.map-null-key.mode' = 'DROP',
  'json.encode.decimal-as-plain-number' = 'true'
)
;

insert into langfarm.tracing.traces
select
id
--,`timestamp`
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from `timestamp`) * 1000 + EXTRACT(MILLISECOND from `timestamp`), 3) as `timestamp`
,name
,project_id
,metadata
,external_id
,user_id
,`release`
,version
,public
,bookmarked
,input
,output
,session_id
,tags
--,created_at
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from created_at) * 1000 + EXTRACT(MILLISECOND from created_at), 3) as created_at
--,updated_at
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from updated_at) * 1000 + EXTRACT(MILLISECOND from updated_at), 3) as updated_at
from kafka_traces_source
;