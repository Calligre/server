import logging as log
import os

import boto3
import flask_api

DYNAMO_TABLE = os.environ.get('DYNAMO_TABLE', "calligre-posts")
DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "us-west-2")
dynamo_boto = boto3.Session(profile_name="dynamo")
dynamo = dynamo_boto.resource('dynamodb', region_name=DYNAMO_REGION)\
    .Table(DYNAMO_TABLE)


def inspect_return(r):
    status = r.get("ResponseMetadata", {}).get("HTTPStatusCode", 500)
    if not flask_api.status.is_success(status):
        log.error("Dynamo return != 2xx; wasn't exception: {}".format(status))
        log.error(r)
        r = {"errors": [{"title": "Internal Error", "detail": status}]}
    return r, status


def inspect_error(e):
    log.error(e)
    if not hasattr(e, "response") or e.response.get("Error") is None:
        return {"errors": [{"title": "Internal Error"}]}, \
            flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR
    elif e.response.get("Error").get("Code") == \
            "ConditionalCheckFailedException":
        return {"data": "No changes"}, \
            flask_api.status.HTTP_304_NOT_MODIFIED
    else:
        return {"errors": [{
            "title": e.response.get("Error", {}).get("Code"),
            "detail": e.response.get("Error", {}).get("Message")
            }]}, \
            flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR


def get(params):
    try:
        r = dynamo.query(**params)
        return inspect_return(r)
    except Exception as e:
        return inspect_error(e)


def get_single(params):
    r, status = get(params)

    if not flask_api.status.is_success(status):
        return r, status

    if r.get("Count", 0) != 1:
        return {"errors": [
            {"title": "The post you are trying to access doesn't exist."}]},\
            flask_api.status.HTTP_404_NOT_FOUND

    return r.get("Items"), status


def patch(params):
    try:
        r = dynamo.update_item(**params)
        return inspect_return(r)
    except Exception as e:
        # FIXME： fine grained exception here: ConditionalCheckFailedException
        return inspect_error(e)


def put(params):
    try:
        r = dynamo.put_item(**params)
        return inspect_return(r)
    except Exception as e:
        return inspect_error(e)


def delete(params):
    try:
        r = dynamo.delete_item(**params)
        r, status = inspect_return(r)
        if status == 200:
            return None, flask_api.status.HTTP_204_NO_CONTENT
    except Exception as e:
        return inspect_error(e)
