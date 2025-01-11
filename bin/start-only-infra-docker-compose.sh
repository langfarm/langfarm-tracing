#!/bin/sh

docker compose -f docker/docker-compose-only-infra.yml -p langfarm up -d
