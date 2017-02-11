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
                     "organization": "(str, default=None)",
                     "logo": "(str, default=None)",
                     "logo_square": "(str, default=None)",
                     "icon": "(str, default=None)",
                     "color_primary": "(str, default=None)",
                     "color_secondary": "(str, default=None)",
                     "location": "(str, default=None)",
                     "other": "(str, default=None)",
                     "facebook": "(str, default=None)",
                     "twitter": "(str, default=None)",
                     "starttime": "(int, default=None)",
                     "endtime": "(int, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
        req.add_argument('organization', type=str, location='json',
                         default=None)

        req.add_argument('logo', type=str, location='json', default=None)
        req.add_argument('logo_square', type=str, location='json',
                         default=None)
        req.add_argument('icon', type=str, location='json', default=None)

        req.add_argument('color_primary', type=str, location='json',
                         default=None)
        req.add_argument('color_secondary', type=str, location='json',
                         default=None)

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
                         SET (name, organization, logo, logo_square, icon,
                              color_primary, color_secondary, location, other,
                              facebook, twitter, starttime, endtime)
                         VALUES (%(name)s, %(organization)s, %(logo)s,
                                 %(logo_square)s, %(icon)s, %(color_primary)s,
                                 %(color_secondary)s, %(location)s, %(other)s,
                                 %(facebook)s, %(twitter)s, %(starttime)s,
                                 %(endtime)s)
                         WHERE id = %(id)s """,
                     item)

    @requires_auth
    def post(self):
        """{"json": {"name": "(str, required)",
                     "organization": "(str, required)",
                     "logo": "(str, default='')",
                     "logo_square": "(str, default='')",
                     "icon": "(str, default='')",
                     "color_primary": "(str, default='')",
                     "color_secondary": "(str, default='')",
                     "location": "(str, default='')",
                     "other": "(str, default='')",
                     "facebook": "(str, default='')",
                     "twitter": "(str, default='')",
                     "starttime": "(int, required)",
                     "endtime": "(int, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)
        req.add_argument('organization', type=str, location='json',
                         required=True)

        req.add_argument('logo', type=str, location='json', default='')
        req.add_argument('logo_square', type=str, location='json', default='')
        req.add_argument('icon', type=str, location='json', default='')

        req.add_argument('color_primary', type=str, location='json',
                         default='')
        req.add_argument('color_secondary', type=str, location='json',
                         default='')

        req.add_argument('location', type=str, location='json', default='')
        req.add_argument('other', type=str, location='json', default='')

        req.add_argument('facebook', type=str, location='json', default='')
        req.add_argument('twitter', type=str, location='json', default='')

        req.add_argument('starttime', type=int, location='json', required=True)
        req.add_argument('endtime', type=int, location='json', required=True)
        args = req.parse_args()

        return post('info',
                    """ INSERT INTO info (name, organization, logo,
                                          logo_square, icon, color_primary,
                                          color_secondary, location, other,
                                          facebook, twitter, starttime,
                                          endtime)
                        VALUES (%(name)s, %(organization)s, %(logo)s,
                                %(logo_square)s, %(icon)s, %(color_primary)s,
                                %(color_secondary)s, %(location)s, %(other)s,
                                %(facebook)s, %(twitter)s, %(starttime)s,
                                %(endtime)s)
                        RETURNING id """,
                    args)
