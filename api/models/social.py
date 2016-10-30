# pylint: disable=R0201
import time
import random
import string
import os
from decimal import Decimal

import boto3

from boto3.dynamodb.conditions import Attr, Key, Not
import flask_api
import flask_restful
import flask_restful.reqparse

from api import database, dynamo


MAX_POSTS = 25
PROFILE_PIC_BCKT = os.environ.get("PROFILE_PIC_BUCKET", "calligre-profilepics")


def map_id_to_names(uids):
    r, _ = database.gets("user",
                         """SELECT id, first_name, last_name FROM account
                          WHERE id = ANY(%(uids)s);""",
                         {"uids": uids})
    mapping = dict()
    for row in r.get("data"):
        attrs = row.get("attributes")
        mapping[attrs.get("id")] = " ".join((attrs.get("first_name"),
                                             attrs.get("last_name")))
    return mapping


def format_post_response(posts, userid):
    uids = [item["poster_id"] for item in posts]
    uid_mapping = map_id_to_names(uids)

    for item in posts:
        item["timestamp"] = str(item.get("timestamp"))
        item["id"] = item["timestamp"]
        item["poster_name"] = uid_mapping.get(item["poster_id"], "Random User")
        item["poster_icon"] = "https://{}.s3.amazonaws.com/profilepic-{}.jpg".\
            format(PROFILE_PIC_BCKT, item["poster_id"])
        item["current_user_likes"] = userid in item.get("likes", [])
        item["like_count"] = str(item.get("like_count"))
        item.pop("likes", None)
    return posts


def increment_points(userid):
    database.patch("user",
                   "UPDATE account SET points = points + 1 where id = %(id)s",
                   {"id": userid})


def decrement_points(userid):
    database.patch("user",
                   "UPDATE account SET points = points - 1 where id = %(id)s",
                   {"id": userid})


class SocialContentList(flask_restful.Resource):
    def get(self):
        # FIXME: Use userid from jwt token
        userid = "temp id"
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('offset', type=float, location='args', required=False)
        req.add_argument('limit', type=int, location='args', required=False,
                         default=MAX_POSTS)
        args = req.parse_args()

        limit = min(args.get("limit", MAX_POSTS), MAX_POSTS)

        params = {
            "Limit": limit,
            "ScanIndexForward": False,
            "ProjectionExpression":
                "#ts,poster_id,#txt,media_link,like_count,likes",
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

        posts = format_post_response(r.get("Items", []), userid)

        nextOffset = r.get("LastEvaluatedKey", {}).get("timestamp")
        if nextOffset:
            nextOffset = str(nextOffset)

        body = {
            "posts": posts,
            "count": r.get("Count", 0),
            "nextOffset": nextOffset
        }

        return {"data": body}, flask_api.status.HTTP_200_OK

    def post(self):
        # FIXME: Use userid from jwt token
        userid = "test user"
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

        # FIXME: URL mashing to detect the resize bucket usage & change to
        # point at the non-resized bucket
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

        # FIXME: Trigger FB & Twitter Posting Lambdas
        increment_points(userid)
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
        # FIXME: Use userid from jwt token
        userid = "2"
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

        posts = format_post_response(r, userid)

        body = {
            "posts": posts,
            "count": 1,
        }

        return {"data": body}, flask_api.status.HTTP_200_OK

    def delete(self, postid):
        # FIXME: Use userid from jwt token
        userid = "temp id"

        postid = Decimal(postid)
        params = {
            "ProjectionExpression": "poster_id",
            "KeyConditionExpression":
            Key("posts").eq("posts") & Key("timestamp").eq(postid),
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

        decrement_points(userid)

        return dynamo.delete(params)


class SingleSocialContentLikes(flask_restful.Resource):
    def delete(self, postid):
        # FIXME: Use userid from jwt token
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

        decrement_points(userid)

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
        likers = map_id_to_names(liker_ids)

        return {"data": likers}, flask_api.status.HTTP_200_OK

    def post(self, postid):
        # FIXME: Use userid from jwt token
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

        increment_points(userid)

        return dynamo.put(params)
