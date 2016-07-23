# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.database import delete, get, gets, patch, post


class UserList(flask_restful.Resource):
    def get(self):
        return gets('user', 'SELECT * FROM account')

    def post(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)
        req.add_argument('email', type=str, location='json', required=True)

        req.add_argument('description', type=str, location='json', default='')
        req.add_argument('organization', type=str, location='json', default='')
        req.add_argument('photo', type=str, location='json', default='')

        req.add_argument('points', type=int, location='json', default=0)
        req.add_argument('private', type=bool, location='json', default=False)

        req.add_argument('facebook', type=str, location='json', default='')
        req.add_argument('linkedin', type=str, location='json', default='')
        req.add_argument('twitter', type=str, location='json', default='')
        args = req.parse_args()

        return post('user',
                    """ INSERT INTO account (name, email, description,
                                             organization, photo, points,
                                             private, facebook, linkedin,
                                             twitter)
                        VALUES (%(name)s, %(email)s, %(description)s,
                                %(organization)s, %(photo)s, %(points)s,
                                %(private)s, %(facebook)s, %(twitter)s,
                                %(linkedin)s)
                        RETURNING id """,
                    args)


class User(flask_restful.Resource):
    def delete(self, uid):
        return delete('user',
                      'DELETE FROM account WHERE id = %(uid)s',
                      {'uid': uid})

    def get(self, uid):
        return get('user',
                   'SELECT * FROM account WHERE id = %(uid)s',
                   {'uid': uid})

    def patch(self, uid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
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
                         SET (name, email, description, organization, photo,
                              points, private, facebook, linkedin, twitter) =
                             (%(name)s, %(email)s, %(description)s,
                              %(organization)s, %(photo)s, %(points)s,
                              %(private)s, %(facebook)s, %(twitter)s,
                              %(linkedin)s)
                         WHERE id = %(id)s """,
                     item)
