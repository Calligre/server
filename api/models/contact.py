# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_admin, requires_auth
from api.database import delete, get, gets, patch, post


class ContactList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('contact',
                    'SELECT * FROM contact WHERE info_id = %(iid)s',
                    {'iid': 1})

    @requires_auth
    @requires_admin
    def post(self):
        """{"json": {"name": "(str, required)",
                     "phone": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)
        req.add_argument('phone', type=str, location='json', required=True)
        args = req.parse_args()

        args['iid'] = 1

        return post('contact',
                    """ INSERT INTO contact (info_id, name, phone)
                        VALUES (%(iid)s, %(name)s, %(phone)s)
                        RETURNING id """,
                    args)


class Contact(flask_restful.Resource):
    @requires_auth
    @requires_admin
    def delete(self, cid):
        return delete('contact',
                      'DELETE FROM contact WHERE id = %(cid)s',
                      {'cid': cid})

    @requires_auth
    def get(self, cid):
        return get('contact',
                   'SELECT * FROM contact WHERE id = %(cid)s',
                   {'cid': cid})

    @requires_auth
    @requires_admin
    def patch(self, cid):
        """{"json": {"name": "(str, default=None)",
                     "phone": "(str, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
        req.add_argument('phone', type=str, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(cid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('contact',
                     """ UPDATE contact
                         SET (name, phone) = (%(name)s, %(phone)s)
                         WHERE id = %(id)s """,
                     item)
