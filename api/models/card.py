# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import delete, get, gets, patch, post


class CardList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('card',
                    'SELECT * FROM card WHERE info_id = %(iid)s',
                    {'iid': 1})

    @requires_auth
    def post(self):
        """{"json": {"data": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('data', type=str, card='json', required=True)
        args = req.parse_args()

        args['iid'] = 1

        return post('card',
                    """ INSERT INTO card (info_id, data)
                        VALUES (%(iid)s, %(data)s)
                        RETURNING id """,
                    args)


class Card(flask_restful.Resource):
    @requires_auth
    def delete(self, cid):
        return delete('card',
                      'DELETE FROM card WHERE id = %(cid)s',
                      {'cid': cid})

    @requires_auth
    def get(self, cid):
        return get('card',
                   'SELECT * FROM card WHERE id = %(cid)s',
                   {'cid': cid})

    @requires_auth
    def patch(self, cid):
        """{"json": {"data": "(str, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('data', type=str, card='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(cid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('card',
                     'UPDATE card SET (data) = (%(data)s) WHERE id = %(id)s',
                     item)
