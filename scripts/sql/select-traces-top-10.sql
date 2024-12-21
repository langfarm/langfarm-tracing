
SET 'sql-client.execution.result-mode' = 'tableau';
SET 'execution.runtime-mode' = 'batch';
select id, name, input, created_at, updated_at from langfarm.tracing.traces order by created_at desc limit 10;
