# pylint: disable=R0201
import boto3
import flask_api
import flask_restful
import flask_restful.reqparse
import random
import string

from boto3.dynamodb.conditions import Key
from decimal import Decimal

from api.database import delete, get, gets, patch, post


# TODO: parameterize
MAX_POSTS = 25

dynamo_boto = boto3.session(profile_name="dynamo")
dynamo = dynamo_boto.resource('dynamodb', region_name="us-west-2").Table("calligre-posts")

class SocialContentList(flask_restful.Resource):
    def get(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('offset', type=float, location='args', required=False)
        req.add_argument('limit', type=int, location='args', required=False)
        args = req.parse_args()

        limit = args.get("limit", MAX_POSTS)
        limit = min(limit, MAX_POSTS)

        proj = "#ts,poster_id,#txt,media_link,like_count"
        reservedWords = {
            "#ts":"timestamp",
            "#txt": "text"
        }
        params = {
            "Limit": limit,
            "ScanIndexForward": False,
            "ProjectionExpression": proj,
            "ExpressionAttributeNames": reservedWords,
            "KeyConditionExpression": Key("posts").eq("posts") & Key("timestamp").gt(Decimal(0)),
        }

        if args.get("offset"):
            params["ExclusiveStartKey"] = {
                "posts":"posts",
                "timestamp": Decimal(offset)
            }

        r = dynamo.query(**params)

        posts = r.get("Items")
        # Build our details
        for item in posts:
            item['id'] = str(item.get("timestamp"))
            item['poster_name'] = "Lookup Name Result"
            item['poster_icon'] = "http://calligre-profilepics.s3-website-us-west-2.amazonaws.com/profilepic-1.jpg"
            item['current_user_likes'] = True

        nextOffset = r.get("LastEvaluatedKey", {}).get("timestamp")
        if nextOffset is not None:
            nextOffset = str(nextOffset)

        status = r.get("ResponseMetadata", {}).get("HTTPStatusCode", 500)

        if status == 500:
            data = {'errors': [{'title': 'could not communicate with DynamoDB'}]}
            return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

        body = {
            "posts": posts,
            "count": r.get("Count", 0),
            "nextOffset" : nextOffset
        }

        if r.get("Count", 0) == 0:
            return body, flask_api.status.HTTP_404_NOT_FOUND
        else:
            return body, flask_api.status.HTTP_200_OK

    def post(self):
        pass

class SocialContentUploadURL(flask_restful.Resource):
    def get(self):
        s3 = boto3.client('s3')
        post = s3.generate_presigned_post(
            Bucket='calligre-images-pending-resize',
            Key=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
        )
        return post, flask_api.status.HTTP_200_OK

class SingleSocialContent(flask_restful.Resource):
    def get(self, postid):
        proj = "#ts,poster_id,#txt,media_link,like_count"
        reservedWords = {
            "#ts":"timestamp",
            "#txt": "text"
        }
        params = {
            "Limit": limit,
            "ScanIndexForward": False,
            "ProjectionExpression": proj,
            "ExpressionAttributeNames": reservedWords,
            "KeyConditionExpression": Key("posts").eq("posts") & Key("timestamp").eq(Decimal(postid)),
        }

        if args.get("offset"):
            params["ExclusiveStartKey"] = {
                "posts":"posts",
                "timestamp": Decimal(offset)
            }

        r = dynamo.query(**params)

        if r.get("ResponseMetadata", {}).get("HTTPStatusCode", 500) == 500:
            data = {'errors': [{'title': 'could not communicate with DynamoDB'}]}
            return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

        posts = r.get("Items")
        # Build our details
        for item in posts:
            item['id'] = str(item.get("timestamp"))
            item['poster_name'] = "Lookup Name Result"
            item['poster_icon'] = "http://calligre-profilepics.s3-website-us-west-2.amazonaws.com/profilepic-1.jpg"
            item['current_user_likes'] = True

        nextOffset = r.get("LastEvaluatedKey", {}).get("timestamp")
        if nextOffset is not None:
            nextOffset = str(nextOffset)

        body = {
            "posts": posts,
            "count": r.get("Count", 0),
            "nextOffset" : nextOffset
        }

        if r.get("Count", 0) == 0:
            return body, flask_api.status.HTTP_404_NOT_FOUND
        else:
            return body, flask_api.status.HTTP_200_OK

    def delete(self, postid):
        pass
class SingleSocialContentLikes(flask_restful.Resource):
    def delete(self, postid):
        pass

    def get(self, postid):
        pass

    def post(self, postid):
        pass
