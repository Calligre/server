# pylint: disable=R0201
import base64

import boto3
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import delete, get, gets, patch, post


# TODO: parameterize
S3_BUCKET = 'calligre-profilepics'


class UserPhoto(flask_restful.Resource):
    @requires_auth
    def put(self, uid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('data', type=str, location='json', required=True)
        args = req.parse_args()

        filename = 'profilepic-{}.jpg'.format(uid)
        photo = base64.b64decode(args['data'].split(',')[1])

        s3 = boto3.client('s3')
        response = s3.put_object(
            Bucket=S3_BUCKET,
            Key=filename,
            Body=photo,
            ACL='public-read',
            ContentType='image/jpeg'
        )

        if response.get('ResponseMetadata',
                        {}).get('HTTPStatusCode', 500) != 200:
            data = {'errors': [{'title': 'could not communicate with S3'}]}
            return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

        url = 'https://{}.s3.amazonaws.com/{}'.format(S3_BUCKET, filename)
        data = {'data': {'url': url}}
        return data, flask_api.status.HTTP_201_CREATED


class UserList(flask_restful.Resource):
    @requires_auth
    def get(self):
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
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        conds = ["AND {}='{}' ".format(k, v) for k, v in args.items()]
        return gets('user',
                    """ SELECT * FROM account
                        WHERE 1=1 {} """.format(''.join(conds)))

    @requires_auth
    def post(self):
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
        args = req.parse_args()

        return post('user',
                    """ INSERT INTO account (id, first_name, last_name, email,
                                             description, organization, photo,
                                             points, private, facebook,
                                             linkedin, twitter)
                        VALUES (%(id)s, %(first_name)s, %(last_name)s,
                                %(email)s, %(description)s, %(organization)s,
                                %(photo)s, %(points)s, %(private)s,
                                %(facebook)s, %(twitter)s, %(linkedin)s)
                        RETURNING id """,
                    args)


class User(flask_restful.Resource):
    @requires_auth
    def delete(self, uid):
        return delete('user',
                      'DELETE FROM account WHERE id = %(uid)s',
                      {'uid': uid})

    @requires_auth
    def get(self, uid):
        return get('user',
                   'SELECT * FROM account WHERE id = %(uid)s',
                   {'uid': uid})

    @requires_auth
    def patch(self, uid):
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
        args = req.parse_args()

        body, stat = get('user',
                         'SELECT * FROM account WHERE id = %(uid)s',
                         {'uid': uid})
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
                              linkedin, twitter) =
                             (%(first_name)s, %(last_name)s, %(email)s,
                              %(description)s, %(organization)s, %(photo)s,
                              %(points)s, %(private)s, %(facebook)s,
                              %(twitter)s, %(linkedin)s)
                         WHERE id = %(id)s """,
                     item)
