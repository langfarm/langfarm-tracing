#!/bin/sh

/opt/flink/bin/sql-client.sh -i scripts/sql/init-langfarm-db-in-paimon.sql -f scripts/sql/create-tables-in-paimon.sql
