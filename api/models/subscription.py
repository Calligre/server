# pylint: disable=R0201
import flask_restful
import flask_restful.reqparse

from api.database import delete, get, gets, post


class SubscriptionEventList(flask_restful.Resource):
    def get(self, eid):
        return gets('subscription',
                    """ SELECT * FROM subscription
                        WHERE event_id = %(eid)s """,
                    {'eid': eid})

    def post(self, eid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('user_id', type=int, location='json', required=True)
        args = req.parse_args()

        return post('subscription',
                    """ INSERT INTO subscription (account_id, event_id)
                        VALUES (%(uid)s, %(eid)s)
                        RETURNING id """,
                    {'uid': args['user_id'], 'eid': eid})


class SubscriptionUserList(flask_restful.Resource):
    def get(self, uid):
        return gets('subscription',
                    """ SELECT * FROM subscription
                        WHERE account_id = %(uid)s """,
                    {'uid': uid})

    def post(self, uid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('event_id', type=int, location='json', required=True)
        args = req.parse_args()

        return post('subscription',
                    """ INSERT INTO subscription (account_id, event_id)
                        VALUES (%(uid)s, %(eid)s)
                        RETURNING id """,
                    {'uid': uid, 'eid': args['event_id']})


class Subscription(flask_restful.Resource):
    def delete(self, uid, eid):
        return delete('subscription',
                      """ DELETE FROM subscription
                          WHERE account_id = %(uid)s
                              AND event_id = %(eid)s """,
                      {'uid': uid, 'eid': eid})

    def get(self, uid, eid):
        return get('subscription',
                   """ SELECT * FROM subscription
                       WHERE account_id = %(uid)s
                           AND event_id = %(eid)s """,
                   {'uid': uid, 'eid': eid})
