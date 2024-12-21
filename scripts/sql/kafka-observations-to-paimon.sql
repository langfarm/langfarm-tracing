
CREATE TEMPORARY TABLE kafka_observations_source (
    id STRING,
    name STRING,
    start_time TIMESTAMP(6),
    end_time TIMESTAMP(6),
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
    completion_start_time TIMESTAMP(6),
    completion_tokens INT,
    prompt_tokens INT,
    total_tokens INT,
    version STRING,
    project_id STRING,
    created_at TIMESTAMP(6),
    unit STRING,
    prompt_id STRING,
    input_cost numeric(65,30),
    output_cost numeric(65,30),
    total_cost numeric(65,30),
    internal_model STRING,
    updated_at TIMESTAMP(6),
    calculated_input_cost numeric(65,30),
    calculated_output_cost numeric(65,30),
    calculated_total_cost numeric(65,30),
    internal_model_id STRING
)
WITH (
  'connector' = 'kafka',
  'topic' = 'observations',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'kafka-observations-to-paimon',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  'json.map-null-key.mode' = 'DROP',
  'json.encode.decimal-as-plain-number' = 'true'
)
;

insert into langfarm.tracing.observations
select
id
,name
--,start_time
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from start_time) * 1000 + EXTRACT(MILLISECOND from start_time), 3) as start_time
--,end_time
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from end_time) * 1000 + EXTRACT(MILLISECOND from end_time), 3) as end_time
,parent_observation_id
,type
,trace_id
,metadata
,`model`
,modelParameters
,input
,output
,level
,status_message
--,completion_start_time
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from completion_start_time) * 1000 + EXTRACT(MILLISECOND from completion_start_time), 3) as completion_start_time
,completion_tokens
,prompt_tokens
,total_tokens
,version
,project_id
,created_at
,unit
,prompt_id
,input_cost
,output_cost
,total_cost
,internal_model
--,updated_at
,TO_TIMESTAMP_LTZ(EXTRACT(EPOCH from updated_at) * 1000 + EXTRACT(MILLISECOND from updated_at), 3) as updated_at
,calculated_input_cost
,calculated_output_cost
,calculated_total_cost
,internal_model_id
from kafka_observations_source
;