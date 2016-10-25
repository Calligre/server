# Server
"Everything" backend for Calligre -- note that social content is currently
managed as
[Dynamo/Lambda functions](https://github.com/calligre/lambda-functions).

## [API](api/)
Calligre API for non-social content. Social content is managed as Dynamo/Lambda
functions, everything else is here.

### Usage

    pip install -r api/requirements.txt
    python -m api                             # dev
    gunicorn -c api/gunicorn.conf.py api:app  # prod

## [Database](database/)
Config for the Postgres database used by the non-social API.

### Usage

    psql -f database/structure.sql  # migrate database
    psql -f database/dummy.sql      # insert dummy data for testing
