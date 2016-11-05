import logging
import os

import boto3
import flask_api


AWS_DYNAMO_ACCESS_KEY = os.environ.get('AWS_DYNAMO_ACCESS_KEY')
AWS_DYNAMO_SECRET_KEY = os.environ.get('AWS_DYNAMO_SECRET_KEY')

DYNAMO_TABLE = os.environ.get('DYNAMO_TABLE', 'calligre-posts')
DYNAMO_REGION = os.environ.get('DYNAMO_REGION', 'us-west-2')

dynamo_boto = boto3.Session(aws_access_key_id=AWS_DYNAMO_ACCESS_KEY,
                            aws_secret_access_key=AWS_DYNAMO_SECRET_KEY)
dynamo = dynamo_boto.resource('dynamodb',
                              region_name=DYNAMO_REGION).Table(DYNAMO_TABLE)

log = logging.getLogger()
log.setLevel(logging.INFO)


def inspect_return(response):
    status = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)
    if not flask_api.status.is_success(status):
        log.error("Dynamo return != 2xx; wasn't exception: %d", status)
        log.error(response)
        response = {'errors': [{'title': 'internal error',
                                'status': str(status),
                                'detail': 'Dynamo non-exceptional error'}]}

    return response, status


def inspect_error(e):
    log.exception(e)
    if not hasattr(e, 'response') or not e.response.get('Error'):
        data = {'errors': [{'title': 'internal error',
                            'detail': 'no response from Dynamo'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    if e.response.get('Error', {}).get('Code') == \
            'ConditionalCheckFailedException':
        return {'data': None}, flask_api.status.HTTP_304_NOT_MODIFIED

    data = {'errors': [{
        'title': 'internal error',
        'code': e.response.get('Error', {}).get('Code'),
        'detail': e.response.get('Error', {}).get('Message')}]}
    return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR


def get(params):
    try:
        response = dynamo.query(**params)
        return inspect_return(response)
    except Exception as e:
        return inspect_error(e)


def get_single(params):
    response, status = get(params)
    if not flask_api.status.is_success(status):
        return response, status

    if response.get('Count') != 1:
        data = {'errors': [{'title': 'no record found'}]}
        return data, flask_api.status.HTTP_404_NOT_FOUND

    return response.get('Items', {}), status


def patch(params):
    try:
        return inspect_return(dynamo.update_item(**params))
    except Exception as e:
        # FIXME: move fine grained exception here:
        # Need to find type of ConditionalCheckFailedException first
        return inspect_error(e)


def put(params):
    try:
        return inspect_return(dynamo.put_item(**params))
    except Exception as e:
        return inspect_error(e)


def delete(params):
    try:
        response = dynamo.delete_item(**params)
        response, status = inspect_return(response)
        if status == 200:
            return {'data': None}, flask_api.status.HTTP_204_NO_CONTENT

        return response, status
    except Exception as e:
        return inspect_error(e)
