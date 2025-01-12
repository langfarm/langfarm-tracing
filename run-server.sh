#!/bin/sh

uvicorn main:app --host 0.0.0.0 --port 3080 --log-config=logging_dev.yaml
