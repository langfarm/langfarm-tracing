#!/bin/sh

mkdir -p /tmp/langfarm
docker compose -f docker/docker-compose-starrocks.yml -p langfarm-starrocks up -d
