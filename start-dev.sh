#!/bin/sh

export FLASK_ENV=development
export FLASK_APP="doveseed.app:create_app()"
export DOVESEED_CONFIG="config.dev.json"
poetry run flask run
