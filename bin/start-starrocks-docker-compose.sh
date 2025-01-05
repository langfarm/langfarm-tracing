#!/bin/sh

mkdir -p /tmp/minio
docker compose -f docker-compose-starrocks.yml -p langfarm-starrocks up -d
