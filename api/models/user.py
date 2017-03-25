# pylint: disable=R0201
import base64
import os

import boto3
from flask import _request_ctx_stack
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_admin, requires_auth
from api.database import delete, gets, patch, post


PROFILE_PIC_BCKT = os.environ.get('PROFILE_PIC_BUCKET', 'calligre-profilepics')


class UserPhoto(flask_restful.Resource):
    @requires_auth
    def put(self, uid):
        """{"json": {"data": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('data', type=str, location='json', required=True)
        args = req.parse_args()

        user_id = _request_ctx_stack.top.current_user['sub']
        if uid != user_id:
            data = {'errors': [{
                'title': 'unauthorized for user action',
                'detail': 'may only manage own user'}]}
            return data, flask_api.status.HTTP_403_FORBIDDEN

        filename = 'profilepic-{}.jpg'.format(uid)
        photo = base64.b64decode(args['data'].split(',')[1])

        s3 = boto3.client('s3')
        response = s3.put_object(
            Bucket=PROFILE_PIC_BCKT,
            Key=filename,
            Body=photo,
            ACL='public-read',
            ContentType='image/jpeg'
        )

        if response.get('ResponseMetadata',
                        {}).get('HTTPStatusCode', 500) != 200:
            data = {'errors': [{'title': 'could not communicate with S3'}]}
            return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

        url = 'https://{}.s3.amazonaws.com/{}'.\
            format(PROFILE_PIC_BCKT, filename)
        data = {'data': {'url': url}}
        return data, flask_api.status.HTTP_201_CREATED


class UserList(flask_restful.Resource):
    @requires_auth
    def get(self):
        """{"args": {"first_name": "(str, default=None)",
                     "last_name": "(str, default=None)",
                     "email": "(str, default=None)",
                     "description": "(str, default=None)",
                     "organization": "(str, default=None)",
                     "photo": "(str, default=None)",
                     "points": "(int, default=None)",
                     "private": "(bool, default=None)",
                     "facebook": "(str, default=None)",
                     "linkedin": "(str, default=None)",
                     "twitter": "(str, default=None)",
                     "capabilities": "(int, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('first_name', type=str, location='args', default=None)
        req.add_argument('last_name', type=str, location='args', default=None)
        req.add_argument('email', type=str, location='args', default=None)

        req.add_argument('description', type=str, location='args',
                         default=None)
        req.add_argument('organization', type=str, location='args',
                         default=None)
        req.add_argument('photo', type=str, location='args', default=None)

        req.add_argument('points', type=int, location='args', default=None)
        req.add_argument('private', type=bool, location='args', default=None)

        req.add_argument('facebook', type=str, location='args', default=None)
        req.add_argument('linkedin', type=str, location='args', default=None)
        req.add_argument('twitter', type=str, location='args', default=None)

        req.add_argument('capabilities', type=int, location='args',
                         default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        conds = ["AND {}='{}' ".format(k, v) for k, v in args.items()]
        return gets('user',
                    """ SELECT *, ROW_NUMBER()
                                      OVER (ORDER BY points DESC)
                                      AS rank
                        FROM account
                        WHERE 1=1 {} """.format(''.join(conds)))

    @requires_auth
    def post(self):
        """{"json": {"id": "(str, required)",
                     "first_name": "(str, required)",
                     "last_name": "(str, required)",
                     "email": "(str, required)",
                     "description": "(str, default='')",
                     "organization": "(str, default='')",
                     "photo": "(str, default='default.gif')",
                     "points": "(int, default=0)",
                     "private": "(bool, default=False)",
                     "facebook": "(str, default='')",
                     "linkedin": "(str, default='')",
                     "twitter": "(str, default='')",
                     "capabilities": "(int, default=1)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('id', type=str, location='json', required=True)
        req.add_argument('first_name', type=str, location='json',
                         required=True)
        req.add_argument('last_name', type=str, location='json', required=True)
        req.add_argument('email', type=str, location='json', required=True)

        req.add_argument('description', type=str, location='json', default='')
        req.add_argument('organization', type=str, location='json', default='')
        req.add_argument(
            'photo', type=str, location='json',
            default='https://u.o0bc.com/avatars/stock/_no-user-image.gif')

        req.add_argument('points', type=int, location='json', default=0)
        req.add_argument('private', type=bool, location='json', default=False)

        req.add_argument('facebook', type=str, location='json', default='')
        req.add_argument('linkedin', type=str, location='json', default='')
        req.add_argument('twitter', type=str, location='json', default='')

        req.add_argument('capabilities', type=int, location='json', default=1)
        args = req.parse_args()

        user_id = _request_ctx_stack.top.current_user['sub']
        if args['id'] != user_id:
            args['id'] = user_id

        return post('user',
                    """ INSERT INTO account (id, first_name, last_name, email,
                                             description, organization, photo,
                                             points, private, facebook,
                                             linkedin, twitter, capabilities)
                        VALUES (%(id)s, %(first_name)s, %(last_name)s,
                                %(email)s, %(description)s, %(organization)s,
                                %(photo)s, %(points)s, %(private)s,
                                %(facebook)s, %(linkedin)s, %(twitter)s,
                                %(capabilities)s)
                        RETURNING id """,
                    args)


class User(flask_restful.Resource):
    @requires_auth
    @requires_admin
    def delete(self, uid):
        return delete('user',
                      'DELETE FROM account WHERE id = %(uid)s',
                      {'uid': uid})

    @requires_auth
    def get(self, uid):
        body, stat = gets('user',
                          """ SELECT *, ROW_NUMBER()
                                            OVER (ORDER BY points DESC)
                                            AS rank
                              FROM account """)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        record = None
        for k in body['data']:
            if k['id'] == uid:
                record = k
                break

        if not record:
            data = {'errors': [{'title': 'no record found'}]}
            return data, flask_api.status.HTTP_404_NOT_FOUND

        return {'data': record}, flask_api.status.HTTP_200_OK

    @requires_auth
    def patch(self, uid):
        """{"json": {"first_name": "(str, default=None)",
                     "last_name": "(str, default=None)",
                     "email": "(str, default=None)",
                     "description": "(str, default=None)",
                     "organization": "(str, default=None)",
                     "photo": "(str, default=None)",
                     "points": "(int, default=None)",
                     "private": "(bool, default=None)",
                     "facebook": "(str, default=None)",
                     "linkedin": "(str, default=None)",
                     "twitter": "(str, default=None)",
                     "capabilities": "(int, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('first_name', type=str, location='json', default=None)
        req.add_argument('last_name', type=str, location='json', default=None)
        req.add_argument('email', type=str, location='json', default=None)

        req.add_argument('description', type=str, location='json',
                         default=None)
        req.add_argument('organization', type=str, location='json',
                         default=None)
        req.add_argument('photo', type=str, location='json', default=None)

        req.add_argument('points', type=int, location='json', default=None)
        req.add_argument('private', type=bool, location='json', default=None)

        req.add_argument('facebook', type=str, location='json', default=None)
        req.add_argument('linkedin', type=str, location='json', default=None)
        req.add_argument('twitter', type=str, location='json', default=None)

        req.add_argument('capabilities', type=int, location='json',
                         default=None)
        args = req.parse_args()

        user_id = _request_ctx_stack.top.current_user['sub']
        if uid != user_id:
            data = {'errors': [{
                'title': 'unauthorized for user action',
                'detail': 'may only manage own user'}]}
            return data, flask_api.status.HTTP_403_FORBIDDEN

        body, stat = self.get(uid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            if v is not None:
                item[k] = v

        return patch('user',
                     """ UPDATE account
                         SET (first_name, last_name, email, description,
                              organization, photo, points, private, facebook,
                              linkedin, twitter, capabilities) =
                             (%(first_name)s, %(last_name)s, %(email)s,
                              %(description)s, %(organization)s, %(photo)s,
                              %(points)s, %(private)s, %(facebook)s,
                              %(linkedin)s, %(twitter)s, %(capabilities)s)
                         WHERE id = %(id)s """,
                     item)
