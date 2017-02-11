# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import delete, get, patch, post


class Info(flask_restful.Resource):
    @requires_auth
    def delete(self):
        return delete('info',
                      'DELETE FROM info WHERE id = %(iid)s',
                      {'iid': 1})

    @requires_auth
    def get(self):
        return get('info',
                   'SELECT * FROM info WHERE id = %(iid)s',
                   {'iid': 1})

    @requires_auth
    def patch(self):
        """{"json": {"name": "(str, default=None)",
                     "logo": "(str, default=None)",
                     "location": "(str, default=None)",
                     "other": "(str, default=None)",
                     "facebook": "(str, default=None)",
                     "twitter": "(str, default=None)",
                     "starttime": "(int, default=None)",
                     "endtime": "(int, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)

        req.add_argument('logo', type=str, location='json', default=None)
        req.add_argument('location', type=str, location='json', default=None)
        req.add_argument('other', type=str, location='json', default=None)

        req.add_argument('facebook', type=str, location='json', default=None)
        req.add_argument('twitter', type=str, location='json', default=None)

        req.add_argument('starttime', type=int, location='json', default=None)
        req.add_argument('endtime', type=int, location='json', default=None)
        args = req.parse_args()

        body, stat = self.get()
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            if v is not None:
                item[k] = v

        return patch('info',
                     """ UPDATE info
                         SET (name, logo, location, other, facebook, twitter,
                              starttime, endtime) =
                             (%(name)s, %(logo)s, %(location)s, %(other)s,
                              %(facebook)s, %(twitter)s, %(starttime)s,
                              %(endtime)s)
                         WHERE id = %(id)s """,
                     item)

    @requires_auth
    def post(self):
        """{"json": {"name": "(str, required)",
                     "logo": "(str, default='')",
                     "location": "(str, default='')",
                     "other": "(str, default='')",
                     "facebook": "(str, default='')",
                     "twitter": "(str, default='')",
                     "starttime": "(int, required)",
                     "endtime": "(int, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)

        req.add_argument('logo', type=str, location='json', default='')
        req.add_argument('location', type=str, location='json', default='')
        req.add_argument('other', type=str, location='json', default='')

        req.add_argument('facebook', type=str, location='json', default='')
        req.add_argument('twitter', type=str, location='json', default='')

        req.add_argument('starttime', type=int, location='json', required=True)
        req.add_argument('endtime', type=int, location='json', required=True)
        args = req.parse_args()

        return post('info',
                    """ INSERT INTO info (name, logo, location, other,
                                          facebook, twitter, starttime,
                                          endtime)
                        VALUES (%(name)s, %(logo)s, %(location)s, %(other)s,
                                %(facebook)s, %(twitter)s, %(starttime)s,
                                %(endtime)s)
                        RETURNING id """,
                    args)
