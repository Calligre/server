# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_admin, requires_auth
from api.database import delete, get, gets, patch, post


class SponsorList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('sponsor',
                    'SELECT * FROM sponsor WHERE info_id = %(iid)s',
                    {'iid': 1})

    @requires_auth
    @requires_admin
    def post(self):
        """{"json": {"name": "(str, required)",
                     "logo": "(str, required)",
                     "level": "(str, default='')",
                     "website": "(str, default='')"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, sponsor='json', required=True)
        req.add_argument('logo', type=str, sponsor='json', required=True)

        req.add_argument('level', type=str, sponsor='json', default='')
        req.add_argument('website', type=str, sponsor='json', default='')
        args = req.parse_args()

        args['iid'] = 1

        return post('sponsor',
                    """ INSERT INTO sponsor (info_id, name, logo, level,
                                             website)
                        VALUES (%(iid)s, %(name)s, %(logo)s, %(level)s,
                                %(website)s)
                        RETURNING id """,
                    args)


class Sponsor(flask_restful.Resource):
    @requires_auth
    @requires_admin
    def delete(self, sid):
        return delete('sponsor',
                      'DELETE FROM sponsor WHERE id = %(sid)s',
                      {'sid': sid})

    @requires_auth
    def get(self, sid):
        return get('sponsor',
                   'SELECT * FROM sponsor WHERE id = %(sid)s',
                   {'sid': sid})

    @requires_auth
    @requires_admin
    def patch(self, sid):
        """{"json": {"name": "(str, default=None)",
                     "logo": "(str, default=None)",
                     "level": "(str, default=None)",
                     "website": "(str, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, sponsor='json', default=None)
        req.add_argument('logo', type=str, sponsor='json', default=None)

        req.add_argument('level', type=str, sponsor='json', default=None)
        req.add_argument('website', type=str, sponsor='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(sid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('sponsor',
                     """ UPDATE sponsor
                         SET (name, logo, level, website) =
                             (%(name)s, %(logo)s, %(level)s, %(website)s)
                         WHERE id = %(id)s """,
                     item)
