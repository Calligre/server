# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import delete, get, gets, patch, post


class EventList(flask_restful.Resource):
    @requires_auth
    def get(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='args', default=None)

        req.add_argument('location', type=str, location='args', default=None)
        req.add_argument('stream', type=int, location='args', default=None)

        req.add_argument('starttime', type=int, location='args', default=None)
        req.add_argument('endtime', type=int, location='args', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        conds = ["AND {}='{}' ".format(k, v) for k, v in args.items()]
        return gets('event',
                    'SELECT * FROM event WHERE 1=1 {}'.format(''.join(conds)))

    @requires_auth
    def post(self):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', required=True)

        req.add_argument('description', type=str, location='json', default='')
        req.add_argument('location', type=str, location='json', default='')
        req.add_argument('stream', type=int, location='json', default=0)

        req.add_argument('starttime', type=int, location='json', required=True)
        req.add_argument('endtime', type=int, location='json', required=True)
        args = req.parse_args()

        return post('event',
                    """ INSERT INTO event (name, description, location, stream,
                                           starttime, endtime)
                        VALUES (%(name)s, %(description)s, %(location)s,
                                %(stream)s, %(starttime)s, %(endtime)s)
                        RETURNING id """,
                    args)


class EventUserList(flask_restful.Resource):
    @requires_auth
    def get(self, uid):
        return gets('event',
                    """ SELECT * FROM event
                        INNER JOIN subscription sub ON sub.event_id = event.id
                        WHERE sub.account_id = %(uid)s """,
                    {'uid': uid})


class Event(flask_restful.Resource):
    @requires_auth
    def delete(self, eid):
        return delete('event',
                      'DELETE FROM event WHERE id = %(eid)s',
                      {'eid': eid})

    @requires_auth
    def get(self, eid):
        return get('event',
                   'SELECT * FROM event WHERE id = %(eid)s',
                   {'eid': eid})

    @requires_auth
    def patch(self, eid):
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)

        req.add_argument('description', type=str, location='json',
                         default=None)
        req.add_argument('location', type=str, location='json', default=None)
        req.add_argument('stream', type=int, location='json', default=None)

        req.add_argument('starttime', type=int, location='json', default=None)
        req.add_argument('endtime', type=int, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(eid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('event',
                     """ UPDATE event
                         SET (name, description, location, stream, starttime,
                              endtime) =
                             (%(name)s, %(description)s, %(location)s,
                              %(stream)s, %(starttime)s, %(endtime)s)
                         WHERE id = %(id)s """,
                     item)
