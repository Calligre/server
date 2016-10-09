# Server
Calligre API for non-social content. Social content is managed as Dynamo/Lambda
functions, everything else is here.

## Installation

    pip install -r api/requirements.txt

## Run Commands

### Dev

    ./runapi.py

### Prod

    gunicorn \
        --pid api.pid --bind 0.0.0.0:8080 \
        --access-logfile api.access.log --error-logfile api.error.log \
        --env DB_HOST=$DB_HOST --env DB_PORT=$DB_PORT --env DB_BASE=$DB_NAME --env DB_USER=$DB_USER --env DB_PASS=$DB_PASS \
        --workers 16 --threads 16 \
        api:app --daemon
