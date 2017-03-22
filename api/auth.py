import base64
import functools
import logging
import os

import flask
from flask import _request_ctx_stack
import flask_api
import jwt

from api.database import get


AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', '')
AUTH0_SECRET_ID = os.environ.get('AUTH0_SECRET_ID', '')

log = logging.getLogger()
log.setLevel(logging.INFO)


def decode(token):
    try:
        secret = base64.b64decode(
            AUTH0_SECRET_ID.replace('_', '/').replace('-', '+'))
        payload = jwt.decode(token, secret, audience=AUTH0_CLIENT_ID)
        return payload, flask_api.status.HTTP_200_OK
    except jwt.ExpiredSignature:
        data = {'errors': [{
            'title': 'authorization error',
            'detail': 'expired token'}]}
        return data, flask_api.status.HTTP_401_UNAUTHORIZED
    except jwt.InvalidAudienceError:
        data = {'errors': [{
            'title': 'authorization error',
            'detail': 'incorrect audience'}]}
        return data, flask_api.status.HTTP_401_UNAUTHORIZED
    except jwt.DecodeError:
        data = {'errors': [{
            'title': 'authorization error',
            'detail': 'invalid signature'}]}
        return data, flask_api.status.HTTP_401_UNAUTHORIZED
    except Exception as e:
        log.exception(e)
        data = {'errors': [{
            'title': 'authorization error',
            'detail': 'unknown error occured while parsing authentication',
            'source': {'exception': str(e)}}]}
        return data, flask_api.status.HTTP_401_UNAUTHORIZED


def enabled():
    return AUTH0_CLIENT_ID and AUTH0_SECRET_ID


def requires_admin(function):
    @functools.wraps(function)
    def decorated(*args, **kwargs):
        payload = _request_ctx_stack.top.current_user
        if not payload:
            data = {'errors': [{
                'title': 'authorization error',
                'detail': 'user is not logged in'}]}
            return data, flask_api.status.HTTP_401_UNAUTHORIZED

        if payload['cap'] < 4:
            data = {'errors': [{
                'title': 'access denied',
                'detail': 'user is not an admin'}]}
            return data, flask_api.status.HTTP_403_FORBIDDEN

        return function(*args, **kwargs)

    return decorated


def requires_auth(function):
    # pylint: disable=too-many-return-statements
    @functools.wraps(function)
    def decorated(*args, **kwargs):
        if not enabled():
            _request_ctx_stack.top.current_user = {
                'aud': AUTH0_CLIENT_ID,
                'exp': 4102444800,  # 2100-01-01
                'iat': 946684800,   # 2000-01-01
                'iss': 'https://calligre.auth0.com/',
                'sub': '1',         # user ID
                'cap': 7,
            }
            return function(*args, **kwargs)

        auth = flask.request.headers.get('Authorization', None)
        if not auth:
            data = {'errors': [{
                'title': 'authorization error',
                'detail': 'missing authorization header'}]}
            return data, flask_api.status.HTTP_401_UNAUTHORIZED

        parts = auth.split()
        if len(parts) != 2:
            data = {'errors': [{
                'title': 'authorization error',
                'detail': 'authorization header is malformed'}]}
            return data, flask_api.status.HTTP_401_UNAUTHORIZED

        bearer, token = parts
        if bearer.lower() != 'bearer':
            data = {'errors': [{
                'title': 'authorization error',
                'detail': 'authorization header must start with Bearer'}]}
            return data, flask_api.status.HTTP_401_UNAUTHORIZED

        payload, status = decode(token)
        if not flask_api.status.is_success(status):
            return payload, status

        body, status = get('user',
                           """ SELECT capabilities
                               FROM account
                               WHERE id = %(sub)s
                           """, payload)
        if flask_api.status.is_success(status):
            payload['cap'] = int(body['data']['capabilities'])
        else:
            log.warning('Attempted admin access from "%s"', payload['sub'])
            payload['cap'] = 0

        _request_ctx_stack.top.current_user = payload
        return function(*args, **kwargs)

    return decorated
