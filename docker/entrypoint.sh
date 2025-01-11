#!/bin/sh

source ~/.bashrc

mkdir -p logs
poetry run uvicorn main:app --host 0.0.0.0 --port 3080 --log-config=logging.yaml
