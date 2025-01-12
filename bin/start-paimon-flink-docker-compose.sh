#!/bin/sh

mkdir -p /tmp/langfarm/flink
mkdir -p /tmp/langfarm/paimon

docker compose -f docker/docker-compose-paimon-flink.yml -p langfarm-paimon-flink up -d
