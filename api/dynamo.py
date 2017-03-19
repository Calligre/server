import logging
import os

import boto3
import flask_api


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
    # ConditionalCheckFailedException is an expected thing, don't log it
    if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == \
            'ConditionalCheckFailedException':
        return {'data': None}, flask_api.status.HTTP_304_NOT_MODIFIED

    log.exception(e)
    if not hasattr(e, 'response') or not e.response.get('Error'):
        data = {'errors': [{'title': 'internal error',
                            'detail': 'no response from Dynamo'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    data = {'errors': [{
        'title': 'internal error',
        'code': e.response.get('Error', {}).get('Code'),
        'detail': e.response.get('Error', {}).get('Message')}]}
    return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR


def expect_empty_return(response):
    response, status = inspect_return(response)
    if status == 200:
        return {'data': None}, flask_api.status.HTTP_204_NO_CONTENT
    return response, status


class DynamoWrapper:
    def __init__(self,
                 table=os.environ.get('DYNAMO_TABLE', 'calligre-posts'),
                 region=os.environ.get('DYNAMO_REGION', 'us-west-2'),
                 access_key=os.environ.get('AWS_DYNAMO_ACCESS_KEY'),
                 secret_key=os.environ.get('AWS_DYNAMO_SECRET_KEY')):

        self._boto = boto3.Session(aws_access_key_id=access_key,
                                   aws_secret_access_key=secret_key)
        self.dynamo = self._boto.resource('dynamodb',
                                          region_name=region).Table(table)

    def get(self, params):
        try:
            return inspect_return(self.dynamo.query(**params))
        except Exception as e:
            return inspect_error(e)

    def get_single(self, params):
        response, status = self.get(params)
        if not flask_api.status.is_success(status):
            return response, status

        if response.get('Count') != 1:
            data = {'errors': [{'title': 'no record found'}]}
            return data, flask_api.status.HTTP_404_NOT_FOUND

        return response.get('Items', {}), status

    def patch(self, params):
        try:
            return expect_empty_return(self.dynamo.update_item(**params))
        except Exception as e:
            return inspect_error(e)

    def put(self, params):
        try:
            return expect_empty_return(self.dynamo.put_item(**params))
        except Exception as e:
            return inspect_error(e)

    def delete(self, params):
        try:
            return expect_empty_return(self.dynamo.delete_item(**params))
        except Exception as e:
            return inspect_error(e)
