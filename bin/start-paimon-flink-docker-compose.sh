#!/bin/sh

docker compose -f docker-compose-paimon-flink.yml -p langfarm-paimon-flink up -d
