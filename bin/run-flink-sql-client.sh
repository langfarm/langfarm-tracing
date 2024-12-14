#!/bin/sh

docker compose -f docker-compose-flink-sql-client.yml run --rm sql-client /bin/bash
