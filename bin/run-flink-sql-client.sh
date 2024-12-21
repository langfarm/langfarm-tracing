#!/bin/sh

mkdir -p /tmp/langfarm-tracing
docker compose -f docker-compose-flink-sql-client.yml run --rm sql-client /bin/bash
