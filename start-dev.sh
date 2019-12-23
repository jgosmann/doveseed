#!/bin/sh

export FLASK_ENV=development
export FLASK_APP="doveseed.app:create_app_local_dev()"
poetry run flask run
