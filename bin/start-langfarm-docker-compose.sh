#!/bin/sh

mkdir -p /tmp/langfarm
docker compose -f docker/docker-compose.yml -p langfarm up -d
