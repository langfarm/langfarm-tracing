#!/bin/sh

mkdir -p /tmp/langfarm/flink
mkdir -p /tmp/langfarm/paimon
docker compose -f docker/docker-compose-flink-sql-client.yml run --rm sql-client /bin/bash
