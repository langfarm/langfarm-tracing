
SET 'sql-client.execution.result-mode' = 'tableau';
SET 'execution.runtime-mode' = 'batch';
select id, name, REGEXP_REPLACE(input, '\n', ' ') as input, created_at, updated_at from langfarm.tracing.observations order by created_at desc limit 10;
