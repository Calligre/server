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
                     "map": "(str, default=None)",
                     "package": "(str, default=None)",
                     "logo": "(str, default=None)",
                     "logo_square": "(str, default=None)",
                     "background_logo": "(str, default=None)",
                     "icon": "(str, default=None)",
                     "color_primary": "(str, default=None)",
                     "color_secondary": "(str, default=None)",
                     "facebook": "(str, default=None)",
                     "twitter": "(str, default=None)",
                     "starttime": "(int, default=None)",
                     "endtime": "(int, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
        req.add_argument('organization', type=str, location='json',
                         default=None)

        req.add_argument('map', type=str, location='json', default=None)
        req.add_argument('package', type=str, location='json', default=None)

        req.add_argument('logo', type=str, location='json', default=None)
        req.add_argument('logo_square', type=str, location='json',
                         default=None)
        req.add_argument('background_logo', type=str, location='json',
                         default=None)
        req.add_argument('icon', type=str, location='json', default=None)

        req.add_argument('color_primary', type=str, location='json',
                         default=None)
        req.add_argument('color_secondary', type=str, location='json',
                         default=None)

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
                         SET (name, organization, map, package, logo,
                              logo_square, background_logo, icon,
                              color_primary, color_secondary, facebook,
                              twitter, starttime, endtime) =
                             (%(name)s, %(organization)s, %(map)s, %(package)s,
                              %(logo)s, %(logo_square)s, %(background_logo)s,
                              %(icon)s, %(color_primary)s, %(color_secondary)s,
                              %(facebook)s, %(twitter)s, %(starttime)s,
                              %(endtime)s)
                         WHERE id = %(id)s """,
                     item)

    @requires_auth
    def post(self):
        """{"json": {"name": "(str, required)",
                     "organization": "(str, required)",
                     "map": "(str, default='')",
                     "package": "(str, default='')",
                     "logo": "(str, default='')",
                     "logo_square": "(str, default='')",
                     "background_logo": "(str, default='')",
                     "icon": "(str, default='')",
                     "color_primary": "(str, default='')",
                     "color_secondary": "(str, default='')",
                     "facebook": "(str, default='')",
                     "twitter": "(str, default='')",
                     "starttime": "(int, required)",
                     "endtime": "(int, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)
        req.add_argument('organization', type=str, location='json',
                         required=True)

        req.add_argument('map', type=str, location='json', default='')
        req.add_argument('package', type=str, location='json', default='')

        req.add_argument('logo', type=str, location='json', default='')
        req.add_argument('logo_square', type=str, location='json', default='')
        req.add_argument('background_logo', type=str, location='json',
                         default='')
        req.add_argument('icon', type=str, location='json', default='')

        req.add_argument('color_primary', type=str, location='json',
                         default='')
        req.add_argument('color_secondary', type=str, location='json',
                         default='')

        req.add_argument('facebook', type=str, location='json', default='')
        req.add_argument('twitter', type=str, location='json', default='')

        req.add_argument('starttime', type=int, location='json', required=True)
        req.add_argument('endtime', type=int, location='json', required=True)
        args = req.parse_args()

        return post('info',
                    """ INSERT INTO info (name, organization, map, package,
                                          logo, logo_square, background_logo
                                          icon, color_primary, color_secondary,
                                          facebook, twitter, starttime,
                                          endtime)
                        VALUES (%(name)s, %(organization)s, %(map)s,
                                %(package)s, %(logo)s, %(logo_square)s,
                                %(icon)s, %(color_primary)s,
                                %(color_secondary)s, %(facebook)s, %(twitter)s,
                                %(starttime)s, %(endtime)s)
                        RETURNING id """,
                    args)
