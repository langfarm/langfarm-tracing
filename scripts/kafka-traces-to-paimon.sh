#!/bin/sh

/opt/flink/bin/sql-client.sh -i scripts/sql/init-langfarm-db.sql -f scripts/sql/kafka-traces-to-paimon.sql
