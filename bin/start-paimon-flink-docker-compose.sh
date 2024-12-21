#!/bin/sh

mkdir -p /tmp/langfarm-tracing
docker compose -f docker-compose-paimon-flink.yml -p langfarm-paimon-flink up -d
