# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.database import delete, get, gets, patch, post


class BroadcastList(flask_restful.Resource):
    def get(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('expirytime', type=int, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        conds = ["AND {}='{}' ".format(k, v) for k, v in args.items()]
        return gets('broadcast',
                    """ SELECT * FROM broadcast
                        WHERE 1=1 {} """.format(''.join(conds)))

    def post(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('message', type=str, location='json', required=True)
        req.add_argument('expirytime', type=int, location='json',
                         required=True)
        args = req.parse_args()

        return post('broadcast',
                    """ INSERT INTO broadcast (message, expirytime)
                        VALUES (%(message)s, %(expirytime)s)
                        RETURNING id """,
                    args)


class Broadcast(flask_restful.Resource):
    def delete(self, bid):
        return delete('broadcast',
                      'DELETE FROM broadcast WHERE id = %(bid)s',
                      {'bid': bid})

    def get(self, bid):
        return get('broadcast',
                   'SELECT * FROM broadcast WHERE id = %(bid)s',
                   {'bid': bid})

    def patch(self, bid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('message', type=str, location='json', default=None)
        req.add_argument('expirytime', type=int, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = get('broadcast',
                         'SELECT * FROM broadcast WHERE id = %(bid)s',
                         {'bid': bid})
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('broadcast',
                     """ UPDATE broadcast
                         SET (message, expirytime) =
                             (%(message)s, %(expirytime)s)
                         WHERE id = %(id)s """,
                     item)
