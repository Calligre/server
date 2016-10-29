# pylint: disable=R0201
import time
import random
import string
import logging as log
from decimal import Decimal

import boto3

from boto3.dynamodb.conditions import Attr, Key, Not
import flask_api
import flask_restful
import flask_restful.reqparse

from api import database, dynamo


MAX_POSTS = 25


def format_post_response(posts):
    # FIXME: Lookup name & profile pic location for each poster
    for item in posts:
        item["timestamp"] = str(item.get("timestamp"))
        item["id"] = item["timestamp"]
        item["poster_name"] = "Lookup Name Result"
        item["poster_icon"] = \
            "http://calligre-profilepics.s3-website-us-west-2.amazonaws.com/profilepic-1.jpg"
        item["current_user_likes"] = True
        item["like_count"] = str(item.get("like_count"))
    return posts


class SocialContentList(flask_restful.Resource):
    def get(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('offset', type=float, location='args', required=False)
        req.add_argument('limit', type=int, location='args', required=False,
                         default=MAX_POSTS)
        args = req.parse_args()

        limit = min(args.get("limit", MAX_POSTS), MAX_POSTS)

        params = {
            "Limit": limit,
            "ScanIndexForward": False,
            "ProjectionExpression": "#ts,poster_id,#txt,media_link,like_count",
            "ExpressionAttributeNames": {
                "#ts": "timestamp",
                "#txt": "text"
            },
            "KeyConditionExpression":
            Key("posts").eq("posts") & Key("timestamp").gt(Decimal(0)),
        }

        if args.get("offset"):
            params["ExclusiveStartKey"] = {
                "posts": "posts",
                "timestamp": Decimal(args.get("offset"))
            }

        r, status = dynamo.get(params)

        if not flask_api.status.is_success(status):
            return r, status

        posts = format_post_response(r.get("Items", []))

        nextOffset = r.get("LastEvaluatedKey", {}).get("timestamp")
        if nextOffset is not None:
            nextOffset = str(nextOffset)

        body = {
            "posts": posts,
            "count": r.get("Count", 0),
            "nextOffset": nextOffset
        }

        return {"data": body}, flask_api.status.HTTP_200_OK

    def post(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('text', type=str, location='json', default=None,
                         required=True)
        req.add_argument('media_link', type=str, location='json', default=None)
        req.add_argument('post_fb', type=bool, location='json', default=False)
        req.add_argument('post_tw', type=bool, location='json', default=False)
        args = req.parse_args()

        if not (args.get("text") or args.get("media_link")):
            return {"errors": [{
                "title": "You must provide either text or a media URL."}]}, \
                flask_api.status.HTTP_400_BAD_REQUEST

        timestamp = Decimal(time.time())
        params = {
            "Item": {
                "posts": "posts",
                "timestamp": timestamp,
                "poster_id": "temp id",
                "like_count": 0,
                "text": args.get("text"),
                "media_link": args.get("media_link")
            },
            "ConditionExpression": Attr("timestamp").ne(timestamp)
        }

        r, status = dynamo.put(params)

        if not flask_api.status.is_success(status):
            return r, status

        return {"data": {"id": str(timestamp)}}, flask_api.status.HTTP_200_OK


class SocialContentUploadURL(flask_restful.Resource):
    def get(self):
        s3 = boto3.client('s3')
        post_url = s3.generate_presigned_post(
            Bucket='calligre-images-pending-resize',
            Key=''.join(random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(12))
        )
        return post_url, flask_api.status.HTTP_200_OK


class SingleSocialContent(flask_restful.Resource):
    def get(self, postid):
        params = {
            "Limit": 1,
            "ScanIndexForward": False,
            "ProjectionExpression": "#ts,poster_id,#txt,media_link,like_count",
            "ExpressionAttributeNames": {
                "#ts": "timestamp",
                "#txt": "text"
            },
            "KeyConditionExpression":
            Key("posts").eq("posts") & Key("timestamp").eq(Decimal(postid)),
        }

        r, status = dynamo.get_single(params)

        if not flask_api.status.is_success(status):
            return r, status

        posts = format_post_response(r)

        body = {
            "posts": posts,
            "count": 1,
        }

        return {"data": body}, flask_api.status.HTTP_200_OK

    def delete(self, postid):
        # FIXME
        userid = "temp id"

        postid = Decimal(postid)
        params = {
            "ProjectionExpression": "poster_id",
            "KeyConditionExpression": Key("posts").eq("posts") &
            Key("timestamp").eq(postid),
        }

        r, status = dynamo.get_single(params)

        if not flask_api.status.is_success(status):
            return r, status

        if r[0].get("poster_id") != userid:
            return {"errors": [
                {"title":
                 "The post you are trying to delete isn't owned by you."}
                ]},\
                flask_api.status.HTTP_403_FORBIDDEN

        params = {
            "Key": {
                "posts": "posts",
                "timestamp": postid,
            },
            "ConditionExpression": Attr("poster_id").eq(userid),
            "ReturnItemCollectionMetrics": "SIZE"
        }

        return dynamo.delete(params)


class SingleSocialContentLikes(flask_restful.Resource):
    def delete(self, postid):
        # FIXME
        userid = "test"
        params = {
            "Key": {
                "posts": "posts",
                "timestamp": Decimal(postid),
            },
            "UpdateExpression":
            "DELETE likes :like SET like_count = like_count - :1",
            "ExpressionAttributeValues": {
                ':like': set([userid]),
                ':1': 1
            },
            "ConditionExpression": Attr("likes").contains(userid)
        }
        return dynamo.patch(params)

    def get(self, postid):
        params = {
            "ProjectionExpression": "likers",
            "KeyConditionExpression":
            Key("posts").eq("posts") & Key("timestamp").eq(Decimal(postid)),
        }

        r, status = dynamo.get_single(params)

        if not flask_api.status.is_success(status):
            return r, status

        liker_ids = r[0].get("likers", [])
        # FIXME: SQL lookup: select id, name from users where id in liker_ids
        likers = {
            "temp id": "Testing User 1",
            "temp id 2": "Testing User 2"
        }

        return {"data": likers}, flask_api.status.HTTP_200_OK

    def post(self, postid):
        # FIXME
        userid = "test id"
        params = {
            "Key": {
                "posts": "posts",
                "timestamp": Decimal(postid),
            },
            "UpdateExpression":
            "ADD likes :like SET like_count = like_count + :1",
            "ExpressionAttributeValues": {
                ':like': set([userid]),
                ':1': 1
            },
            "ConditionExpression": Not(Attr("likes").contains(userid))
        }
        return dynamo.put(params)
