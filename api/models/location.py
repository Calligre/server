# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_admin, requires_auth
from api.database import delete, get, gets, patch, post


class LocationList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('location',
                    'SELECT * FROM location WHERE info_id = %(iid)s',
                    {'iid': 1})

    @requires_auth
    @requires_admin
    def post(self):
        """{"json": {"name": "(str, required)",
                     "address": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)
        req.add_argument('address', type=str, location='json', required=True)
        args = req.parse_args()

        args['iid'] = 1

        return post('location',
                    """ INSERT INTO location (info_id, name, address)
                        VALUES (%(iid)s, %(name)s, %(address)s)
                        RETURNING id """,
                    args)


class Location(flask_restful.Resource):
    @requires_auth
    @requires_admin
    def delete(self, lid):
        return delete('location',
                      'DELETE FROM location WHERE id = %(lid)s',
                      {'lid': lid})

    @requires_auth
    def get(self, lid):
        return get('location',
                   'SELECT * FROM location WHERE id = %(lid)s',
                   {'lid': lid})

    @requires_auth
    @requires_admin
    def patch(self, lid):
        """{"json": {"name": "(str, default=None)",
                     "address": "(str, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
        req.add_argument('address', type=str, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(lid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('location',
                     """ UPDATE location
                         SET (name, address) = (%(name)s, %(address)s)
                         WHERE id = %(id)s """,
                     item)
