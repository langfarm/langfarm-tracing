#!/bin/sh

/opt/flink/bin/sql-client.sh -i scripts/sql/init-langfarm-db-in-paimon.sql -f scripts/sql/kafka-observations-to-paimon.sql
