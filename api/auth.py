import base64
import functools
import logging
import os

import flask
from flask import _request_ctx_stack
import flask_api
import jwt


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


def requires_auth(function):
    # pylint: disable=too-many-return-statements
    @functools.wraps(function)
    def decorated(*args, **kwargs):
        if not enabled():
            _request_ctx_stack.top.current_user = 'test-user'
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

        _request_ctx_stack.top.current_user = payload
        return function(*args, **kwargs)

    return decorated
