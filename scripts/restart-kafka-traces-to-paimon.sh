#!/bin/sh

if [ $# -lt 1 ];
then
  echo "usage: $0 <savepoint-id>"
  echo "\texample savepoint path: /data/flink/savepoints/savepoint-f719a5-857cbe1a0ba2, savepoint-id is: f719a5-857cbe1a0ba2"
  exit
fi

/opt/flink/bin/sql-client.sh \
  -Dexecution.state-recovery.path="/data/flink/savepoints/savepoint-$1" \
  -f scripts/sql/kafka-traces-to-paimon.sql
