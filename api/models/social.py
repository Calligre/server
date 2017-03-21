# pylint: disable=R0201
import logging
import os
import random
import string
import time
from decimal import Decimal
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.conditions import Attr, Key, Not
from flask import _request_ctx_stack
import flask_api
import flask_restful
import flask_restful.reqparse

from api import database, dynamo
from api.auth import requires_auth


AWS_SNS_ACCESS_KEY = os.environ.get('AWS_SNS_ACCESS_KEY')
AWS_SNS_SECRET_KEY = os.environ.get('AWS_SNS_SECRET_KEY')

MAX_POSTS = 25
UPLOAD_BUCKET = os.environ.get('UPLOAD_BUCKET', 'calligre-images')
RESIZE_BUCKET = os.environ.get('RESIZE_BUCKET',
                               'calligre-images-pending-resize')
EXT_POSTS_TOPIC = 'arn:aws:sns:us-west-2:037954390517:calligre-external-posts'
DEFAULT_PROFILE_PIC = 'https://s3-us-west-2.amazonaws.com/'
'calligre-profilepics/default.png'
POSTS_TABLE_NAME = os.environ.get('POSTS_TABLE', 'calligre-posts')
FLAG_TABLE_NAME = os.environ.get('FLAGS_TABLE', 'flagged')
posts_table = dynamo.DynamoWrapper(table_name=POSTS_TABLE_NAME)
flag_table = dynamo.DynamoWrapper(table_name=FLAG_TABLE_NAME)

log = logging.getLogger()
log.setLevel(logging.INFO)


def map_id_to_names(uids):
    res, st = database.gets('user',
                            """ SELECT id, first_name, last_name, photo
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

        first_name = attrs.get('first_name', '')
        last_name = attrs.get('last_name', '')
        name = ' '.join([first_name, last_name]).strip()
        profile_pic = attrs.get('photo', DEFAULT_PROFILE_PIC)

        mapping[attrs['id']] = {'name': name,
                                'poster_icon': profile_pic}
    return mapping, st


def format_post_response(posts, req_userid=None):
    uids = [item['poster_id'] for item in posts]
    res, st = map_id_to_names(uids)
    if not flask_api.status.is_success(st):
        return res, st

    for item in posts:
        item['timestamp'] = str(item.get('timestamp'))
        item['id'] = item['timestamp']
        item['poster_name'] = res.get(item['poster_id'], {}).get('name')
        item['poster_icon'] = res.get(item['poster_id'], {}).get('poster_icon')
        item['current_user_likes'] = req_userid in item.get('likes', [])
        item['like_count'] = str(item.get('like_count', 0))
        item['current_user_flagged'] = req_userid in item.get('flags', [])
        item['flag_count'] = str(item.get('flag_count', 0))
        item.pop('likes', None)
        item.pop('flags', None)

    return posts, st


def increment_points(req_userid):
    database.patch('user',
                   'UPDATE account SET points = points + 1 where id = %(id)s',
                   {'id': req_userid})


def decrement_points(req_userid):
    database.patch('user',
                   'UPDATE account SET points = points - 1 where id = %(id)s',
                   {'id': req_userid})


def is_user_mod(userid):
    r, status = database.gets('user',
                              """ SELECT id, capabilities
                                  FROM account
                                  WHERE id = %(id)s """,
                              {'id': str(userid)})
    if not flask_api.status.is_success(status):
        return False
    cap = r['data'].get('attributes', {}).get('capabilities', 0)
    return cap >= 4


class SocialContentList(flask_restful.Resource):
    @requires_auth
    def get(self):
        """{"args": {"limit": "(int, default=25)",
                     "offset": "(float, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('limit', type=int, location='args', default=MAX_POSTS)
        req.add_argument('offset', type=float, location='args', required=False)
        args = req.parse_args()

        limit = min(args['limit'], MAX_POSTS)

        params = {
            'Limit': limit,
            'ScanIndexForward': False,
            'ProjectionExpression': "{},{}".format(
                '#ts,poster_id,#txt,media_link,like_count,likes',
                'flag_count,flags'),
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

        r, status = posts_table.get(params)
        if not flask_api.status.is_success(status):
            return r, status

        userid = _request_ctx_stack.top.current_user['sub']
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
        """{"json": {"text": "(str, default=None)",
                     "media_link": "(str, default=None)",
                     "post_fb": "(bool, default=False)",
                     "post_tw": "(bool, default=False)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('text', type=str, location='json', default=None)
        req.add_argument('media_link', type=str, location='json', default=None)
        req.add_argument('post_fb', type=bool, location='json', default=False)
        req.add_argument('post_tw', type=bool, location='json', default=False)
        args = req.parse_args()

        # FIXME: Might want to validate that we get a valid URL, not just that
        # it's non-empty
        if not (args.get('text') or args.get('media_link')):
            data = {'errors': [{
                'title': 'client error',
                'detail': 'missing text or a media URL.'}]}
            return data, flask_api.status.HTTP_400_BAD_REQUEST

        userid = _request_ctx_stack.top.current_user['sub']
        timestamp = Decimal(time.time())
        params = {
            'Item': {
                'posts': 'posts',
                'timestamp': timestamp,
                'poster_id': userid,
                'like_count': 0,
                'flag_count': 0,
            },
            'ConditionExpression': Attr('timestamp').ne(timestamp),
        }

        if args.get('text'):
            params['Item']['text'] = args.get('text')

        if args.get('media_link'):
            try:
                u = urlparse(args.get('media_link'))
                if u.netloc == "{}.s3.amazonaws.com".format(RESIZE_BUCKET):
                    params['Item']['media_link'] = \
                        "https://{}.s3.amazonaws.com{}".format(
                            UPLOAD_BUCKET,
                            u.path
                        )
                    log.debug("Rewrote %s to %s",
                              args.get('media_link'),
                              params['Item']['media_link'])
                else:
                    params['Item']['media_link'] = args.get('media_link')
            except Exception as ex:
                log.error("Error parsing media link")
                log.exception(ex)

        r, status = posts_table.put(params)
        if not flask_api.status.is_success(status):
            return r, status

        if args.get('post_fb') or args.get('post_tw'):
            self.external_post(userid,
                               args.get('text'),
                               args.get('media_link'),
                               args.get('post_fb', False),
                               args.get('post_tw', False))

        increment_points(userid)
        user_info, _ = map_id_to_names([userid])
        data = {
            'id': str(timestamp),
            'text': params['Item'].get('text'),
            'media_link': params['Item'].get('media_link'),
            'poster_id': userid,
            'poster_name': user_info[userid].get('name'),
            'poster_icon': user_info[userid].get('poster_icon'),
        }
        return {'data': data}, flask_api.status.HTTP_201_CREATED

    @staticmethod
    def external_post(req_userid, message, media_s3, fb, tw):
        params = {
            'TopicArn': EXT_POSTS_TOPIC,
            'Message': message,
            'MessageStructure': 'string',
            'MessageAttributes': {
                'userid': {
                    'DataType': 'String',
                    'StringValue': req_userid
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

        log.debug('%s saying "%s", with media %s',
                  req_userid,
                  message,
                  media_s3)
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
        """{"args": {"Content-Type": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('Content-Type',
                         type=str,
                         location='args',
                         required=True)
        args = req.parse_args()

        userid = _request_ctx_stack.top.current_user['sub']
        suffix = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for _ in range(12))
        post_url = boto3.client('s3').generate_presigned_url(
            "put_object", {
                "Bucket": RESIZE_BUCKET,
                "Key": '{}-{}'.format(userid.replace('|', '-'), suffix),
                "ContentType": args['Content-Type']
            }
        )

        return {'data': post_url}, flask_api.status.HTTP_200_OK


class SingleSocialContent(flask_restful.Resource):
    @requires_auth
    def delete(self, postid):
        postid = Decimal(postid)
        params = {
            'ProjectionExpression': 'poster_id',
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = posts_table.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        userid = _request_ctx_stack.top.current_user['sub']
        is_admin = _request_ctx_stack.top.current_user['cap'] >= 4
        if r[0].get('poster_id') != userid and not is_admin:
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
        return posts_table.delete(params)

    @requires_auth
    def get(self, postid):
        postid = Decimal(postid)
        params = {
            'Limit': 1,
            'ScanIndexForward': False,
            'ProjectionExpression': "{},{}".format(
                '#ts,poster_id,#txt,media_link,like_count,likes',
                'flag_count,flags'),
            'ExpressionAttributeNames': {
                '#ts': 'timestamp',
                '#txt': 'text'
            },
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = posts_table.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        userid = _request_ctx_stack.top.current_user['sub']
        posts = format_post_response(r, userid)

        body = {
            'posts': posts,
            'count': 1,
        }

        return {'data': body}, flask_api.status.HTTP_200_OK


class SingleSocialContentLikes(flask_restful.Resource):
    @requires_auth
    def delete(self, postid):
        userid = _request_ctx_stack.top.current_user['sub']
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

        return posts_table.patch(params)

    @requires_auth
    def get(self, postid):
        postid = Decimal(postid)
        params = {
            'ProjectionExpression': 'likers',
            'KeyConditionExpression':
                Key('posts').eq('posts') & Key('timestamp').eq(postid),
        }

        r, status = posts_table.get_single(params)
        if not flask_api.status.is_success(status):
            return r, status

        liker_ids = r[0].get('likers', [])
        res, st = map_id_to_names(liker_ids)
        if not flask_api.status.is_success(st):
            return res, st

        return {'data': res}, flask_api.status.HTTP_200_OK

    @requires_auth
    def post(self, postid):
        userid = _request_ctx_stack.top.current_user['sub']
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

        return posts_table.patch(params)


class FlaggedPostList(flask_restful.Resource):
    @requires_auth
    def get(self):
        """{"args": {"limit": "(int, default=25)",
                     "offset": "(float, required)"}}"""
        userid = _request_ctx_stack.top.current_user['sub']
        if not is_user_mod(userid):
            return {'data': None}, flask_api.status.HTTP_403_FORBIDDEN
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('limit', type=int, location='args', default=MAX_POSTS)
        req.add_argument('offset', type=float, location='args', required=False)
        args = req.parse_args()

        limit = min(args['limit'], MAX_POSTS)

        params = {
            'Limit': limit,
            'ProjectionExpression': 'timestamp',
        }

        if args.get('offset'):
            params['ExclusiveStartKey'] = {
                'timestamp': Decimal(args.get('offset')),
            }

        r, status = flag_table.scan(params)
        if not flask_api.status.is_success(status):
            return r, status

        # the flagged list might need to be paginated, store the offset now
        nextOffset = r.get('LastEvaluatedKey', {}).get('timestamp')
        if nextOffset:
            nextOffset = str(nextOffset)

        # Format the list of partition + sort keys for batch_get
        post_ids = [{
            'posts': 'posts',
            'timestamp': item['timestamp']
        } for item in r.get('Items', [])]

        params = {'RequestItems': {
            POSTS_TABLE_NAME: {
                'ProjectionExpression':
                    '#ts,poster_id,#txt,media_link,flag_count',
                'ExpressionAttributeNames': {
                    '#ts': 'timestamp',
                    '#txt': 'text'
                },
                'Keys': post_ids
            }
        }}

        r, status = posts_table.batch_get(params)
        if not flask_api.status.is_success(status):
            return r, status
        items = r.get('Responses', {}).get(POSTS_TABLE_NAME, [])

        posts = format_post_response(items)

        body = {
            'posts': posts,
            'count': r.get('Count', 0),
            'nextOffset': nextOffset,
        }

        return {'data': body}, flask_api.status.HTTP_200_OK


class PostFlag(flask_restful.Resource):
    @requires_auth
    def delete(self, postid):
        userid = _request_ctx_stack.top.current_user['sub']
        timestamp = Decimal(postid)
        params = {
            'Key': {
                'posts': 'posts',
                'timestamp': timestamp,
            },
            'UpdateExpression':
                'DELETE flags :flag SET flag_count = flag_count - :1',
            'ExpressionAttributeValues': {
                ':flag': set([userid]),
                ':1': 1
            },
            'ConditionExpression': Attr('flags').contains(userid),
            'ReturnValues': 'UPDATED_NEW',
        }

        r, status = posts_table.patch(params)
        if not flask_api.status.is_success(status):
            return r, status

        if r.get('Attributes', {}).get('flag_count', 0) == 0:
            params = {
                'Key': {
                    'timestamp': timestamp,
                },
            }
            return flag_table.delete(params)

        return {'data': None}, status

    @requires_auth
    def post(self, postid):
        userid = _request_ctx_stack.top.current_user['sub']
        timestamp = Decimal(postid)
        params = {
            'Key': {
                'posts': 'posts',
                'timestamp': timestamp,
            },
            'UpdateExpression':
                'ADD flags :flag SET flag_count = flag_count + :1',
            'ExpressionAttributeValues': {
                ':flag': set([userid]),
                ':1': 1
            },
            'ConditionExpression': Not(Attr('flags').contains(userid)),
        }

        r, status = posts_table.patch(params)
        if not flask_api.status.is_success(status):
            return r, status

        # unconditionally create the flag record because we're only
        # overwritting the parition key attr, which will always be the same
        params = {
            'Item': {
                'timestamp': timestamp,
            },
        }
        return flag_table.put(params)
