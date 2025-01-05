#!/bin/sh

docker exec -it starrocks-fe mysql -P9030 -h127.0.0.1 -uroot --prompt="StarRocks > "

