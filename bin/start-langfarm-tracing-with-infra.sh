#!/bin/sh

docker compose -f docker/docker-compose-with-infra.yml -p langfarm up -d
