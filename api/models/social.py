# pylint: disable=R0201
import logging
import os
import random
import string
import time
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr, Key, Not
import flask_api
import flask_restful
import flask_restful.reqparse

from api import database, dynamo
from api.auth import requires_auth


AWS_SNS_ACCESS_KEY = os.environ.get('AWS_SNS_ACCESS_KEY')
AWS_SNS_SECRET_KEY = os.environ.get('AWS_SNS_SECRET_KEY')

MAX_POSTS = 25
PROFILE_PIC_BCKT = os.environ.get('PROFILE_PIC_BUCKET', 'calligre-profilepics')
EXT_POSTS_TOPIC = 'arn:aws:sns:us-west-2:037954390517:calligre-external-posts'

log = logging.getLogger()
log.setLevel(logging.INFO)


def map_id_to_names(uids):
    res, st = database.gets('user',
                            """ SELECT id, first_name, last_name
                                FROM account
                                WHERE id = ANY(%(uids)s) """,
                            {'uids': uids})
    if not flask_api.status.is_success(st):
        res['errors'].append({
            'title': 'internal error',
            'detail': 'id <-> mapping failed'})
        return res, st

    mapping = dict()
    for row in res.get('data', []):
        attrs = row.get('attributes', {})
        if 'id' not in attrs.keys():
            continue

        mapping[attrs['id']] = ' '.join((attrs.get('first_name', ''),
                                         attrs.get('last_name', '')))

    return mapping, st


def format_post_response(posts, userid):
    uids = [item['poster_id'] for item in posts]
    res, st = map_id_to_names(uids)
    if not flask_api.status.is_success(st):
        return res, st

    for item in posts:
        item['timestamp'] = str(item.get('timestamp'))
        item['id'] = item['timestamp']
        item['poster_name'] = res.get(item['poster_id'], 'Random User')
        item['poster_icon'] = 'https://{}.s3.amazonaws.com/profilepic-{}.jpg'\
            .format(PROFILE_PIC_BCKT, item['poster_id'])
        item['current_user_likes'] = userid in item.get('likes', [])
        item['like_count'] = str(item.get('like_count'))
        item.pop('likes', None)

    return posts, st


def increment_points(userid):
    database.patch('user',
                   'UPDATE account SET points = points + 1 where id = %(id)s',
                   {'id': userid})


def decrement_points(userid):
    database.patch('user',
                   'UPDATE account SET points = points - 1 where id = %(id)s',
                   {'id': userid})


class SocialContentList(flask_restful.Resource):
    @requires_auth
    def get(self):
        # FIXME: Use userid from jwt token
        userid = 'temp id'

        req = flask_restful.reqparse.RequestParser()
        req.add_argument('limit', type=int, location='json', default=MAX_POSTS)
        req.add_argument('offset', type=float, location='json', required=False)
        args = req.parse_args()

        limit = min(args['limit'], MAX_POSTS)

        params = {
            'Limit': limit,
            'ScanIndexForward': False,
            'ProjectionExpression':
                '#ts,poster_id,#txt,media_link,like_count,likes',
            'ExpressionAttributeNames': {
                '#ts': 'timestamp',
                '#txt': 'text'
            },
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').gt(Decimal(0)),
        }

        if args.get('offset'):
            params['ExclusiveStartKey'] = {
                'posts': 'posts',
                'timestamp': Decimal(args.get('offset')),
            }

        r, status = dynamo.get(params)
        if not flask_api.status.is_success(status):
            return r, status

        posts = format_post_response(r.get('Items', []), userid)

        nextOffset = r.get('LastEvaluatedKey', {}).get('timestamp')
        if nextOffset:
            nextOffset = str(nextOffset)

        body = {
            'posts': posts,
            'count': r.get('Count', 0),
            'nextOffset': nextOffset,
        }

        return {'data': body}, flask_api.status.HTTP_200_OK

    @requires_auth
    def post(self):
        # FIXME: Use userid from jwt token
        userid = 'test user'
        # FIXME: Should this be the same key as above?
        other_user_id = 'temp id'

        req = flask_restful.reqparse.RequestParser()
        req.add_argument('text', type=str, location='json', default=None)
        req.add_argument('media_link', type=str, location='json', default=None)
        req.add_argument('post_fb', type=bool, location='json', default=False)
        req.add_argument('post_tw', type=bool, location='json', default=False)
        args = req.parse_args()

        if not (args.get('text') or args.get('media_link')):
            data = {'errors': [{
                'title': 'client error',
                'detail': 'missing text or a media URL.'}]}
            return data, flask_api.status.HTTP_400_BAD_REQUEST

        # FIXME: URL mashing to detect the resize bucket usage & change to
        # point at the non-resized bucket
        # url parse & matching host?
        timestamp = Decimal(time.time())
        params = {
            'Item': {
                'posts': 'posts',
                'timestamp': timestamp,
                'poster_id': other_user_id,
                'like_count': 0,
            },
            'ConditionExpression': Attr('timestamp').ne(timestamp),
        }

        if args.get('text'):
            params['Item']['text'] = args.get('text')

        if args.get('media_link'):
            params['Item']['media_link'] = args.get('media_link')

        r, status = dynamo.put(params)
        if not flask_api.status.is_success(status):
            return r, status

        if args.get('post_fb') or args.get('post_tw'):
            self.external_post(userid,
                               args.get('text'),
                               args.get('media_link'),
                               args.get('post_fb', False),
                               args.get('post_tw', False))

        increment_points(userid)
        return {'data': {'id': str(timestamp)}}, flask_api.status.HTTP_200_OK

    @staticmethod
    def external_post(userid, message, media_s3, fb, tw):
        # FIXME: Use actual userid
        userid = 'facebook|10207943757254134'

        params = {
            'TopicArn': EXT_POSTS_TOPIC,
            'Message': message,
            'MessageStructure': 'string',
            'MessageAttributes': {
                'userid': {
                    'DataType': 'String',
                    'StringValue': userid
                },
                'facebook': {
                    'DataType': 'String',
                    'StringValue': str(fb)
                },
                'twitter': {
                    'DataType': 'String',
                    'StringValue': str(tw)
                },
            },
        }

        if media_s3:
            params['MessageAttributes']['media_s3'] = {
                'DataType': 'String',
                'StringValue': media_s3,
            }

        log.debug("%s saying '%s', with media %s", userid, message, media_s3)
        log.debug('Posting to FB: %s; posting to Twitter: %s', fb, tw)

        try:
            sns_boto = boto3.Session(aws_access_key_id=AWS_SNS_ACCESS_KEY,
                                     aws_secret_access_key=AWS_SNS_SECRET_KEY)
            client = sns_boto.client('sns')
            response = client.publish(**params)
            log.debug('Message sent: %s', response.get('MessageId'))
        except Exception as e:
            log.error('Failed to publish message to SNS!')
            log.exception(e)


class SocialContentUploadURL(flask_restful.Resource):
    @requires_auth
    def get(self):
        # TODO: specify auth?
        s3 = boto3.client('s3')
        post_url = s3.generate_presigned_post(
            Bucket='calligre-images',
            Key=''.join(random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(12))
        )

        return post_url, flask_api.status.HTTP_200_OK


class SingleSocialContent(flask_restful.Resource):
    @requires_auth
    def delete(self, postid):
        # FIXME: Use userid from jwt token
        userid = 'temp id'

        postid = Decimal(postid)
        params = {
            'ProjectionExpression': 'poster_id',
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = dynamo.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        if r[0].get('poster_id') != userid:
            data = {'errors': [{'title': 'client error',
                                'detail': "can not delete un-owned post"}]}
            return data, flask_api.status.HTTP_403_FORBIDDEN

        params = {
            'Key': {
                'posts': 'posts',
                'timestamp': postid,
            },
            'ConditionExpression': Attr('poster_id').eq(userid),
            'ReturnItemCollectionMetrics': 'SIZE',
        }

        decrement_points(userid)

        return dynamo.delete(params)

    @requires_auth
    def get(self, postid):
        # FIXME: Use userid from jwt token
        userid = '2'

        postid = Decimal(postid)
        params = {
            'Limit': 1,
            'ScanIndexForward': False,
            'ProjectionExpression': '#ts,poster_id,#txt,media_link,like_count',
            'ExpressionAttributeNames': {
                '#ts': 'timestamp',
                '#txt': 'text'
            },
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = dynamo.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        posts = format_post_response(r, userid)

        body = {
            'posts': posts,
            'count': 1,
        }

        return {'data': body}, flask_api.status.HTTP_200_OK


class SingleSocialContentLikes(flask_restful.Resource):
    @requires_auth
    def delete(self, postid):
        # FIXME: Use userid from jwt token
        userid = 'test'

        params = {
            'Key': {
                'posts': 'posts',
                'timestamp': Decimal(postid),
            },
            'UpdateExpression':
                'DELETE likes :like SET like_count = like_count - :1',
            'ExpressionAttributeValues': {
                ':like': set([userid]),
                ':1': 1
            },
            'ConditionExpression': Attr('likes').contains(userid),
        }

        decrement_points(userid)

        return dynamo.patch(params)

    @requires_auth
    def get(self, postid):
        postid = Decimal(postid)
        params = {
            'ProjectionExpression': 'likers',
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = dynamo.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        liker_ids = r[0].get('likers', [])
        res, st = map_id_to_names(liker_ids)
        if not flask_api.status.is_success(st):
            return res, st

        return {'data': res}, flask_api.status.HTTP_200_OK

    @requires_auth
    def post(self, postid):
        # FIXME: Use userid from jwt token
        userid = 'test id'

        params = {
            'Key': {
                'posts': 'posts',
                'timestamp': Decimal(postid),
            },
            'UpdateExpression':
                'ADD likes :like SET like_count = like_count + :1',
            'ExpressionAttributeValues': {
                ':like': set([userid]),
                ':1': 1
            },
            'ConditionExpression': Not(Attr('likes').contains(userid))
        }

        increment_points(userid)

        return dynamo.put(params)
