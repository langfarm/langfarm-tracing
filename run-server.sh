#!/bin/sh

uvicorn main:app --reload --log-config=logging_dev.yaml
