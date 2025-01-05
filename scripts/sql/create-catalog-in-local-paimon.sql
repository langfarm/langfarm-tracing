CREATE CATALOG IF NOT EXISTS langfarm WITH (
  'type' = 'paimon',
  'warehouse' = 'file:/data/paimon'
)
;

CREATE DATABASE IF NOT EXISTS langfarm.tracing;
