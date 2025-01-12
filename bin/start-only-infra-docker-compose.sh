#!/bin/sh

# 如果没有 langfarm_default 先创建
# docker network create langfarm_default
docker compose -f docker/docker-compose-only-infra.yml -p langfarm-infra up -d
