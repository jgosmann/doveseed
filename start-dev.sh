#!/bin/sh

export DOVESEED_ENV="development"
export DOVESEED_CONFIG="config.dev.json"
poetry run uvicorn dev:app --reload --port 5000
