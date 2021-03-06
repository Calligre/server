# Server
"Everything" backend for Calligre -- note that some stuff (ie. image resizing)
is currently managed as
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

    psql -f database/structure.down.sql  # migrate database
    psql -f database/structure.up.sql    # migrate database
    psql -f database/dummy.sql           # insert dummy data for testing

## [Proxy](proxy/)
Config for nginx proxy.

### Usage

    docker build -t nginx-proxy proxy/
    docker run -d --net=host -v ${ATTENDEE_WWW_DIR}:/www -v ${SSL_DIR}:/ssl nginx-proxy

Note that `ATTENDEE_WWW_DIR` should point to the build directory of
[attendee-web](https://github.com/calligre/attendee-web) and `SSL_DIR` should
point to the cert folder for the correct subdomain. For example, in prod the
values might be

    export ATTENDEE_WWW_DIR=/home/ec2-user/attendee-web/build
    export SSL_DIR=/home/ec2-user/lets-encrypt-certs/certs/dev.calligre.com
