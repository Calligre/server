# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import get, patch


class Capability(flask_restful.Resource):
    @requires_auth
    def get(self, uid):
        return get('capability',
                   'SELECT * FROM capability WHERE id = %(uid)s',
                   {'uid': uid})

    @requires_auth
    def patch(self, uid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('read', type=bool, location='json', default=None)
        req.add_argument('write', type=bool, location='json', default=None)
        req.add_argument('admin', type=bool, location='json', default=None)
        args = req.parse_args()

        body, stat = get('capability',
                         'SELECT * FROM capability WHERE id = %(uid)s',
                         {'uid': uid})
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            if v is not None:
                item[k] = v

        return patch('capability',
                     """ UPDATE capability
                         SET (read, write, admin) =
                             (%(read)s, %(write)s, %(admin)s)
                         WHERE id = %(id)s """,
                     item)
