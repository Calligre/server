# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_auth
from api.database import delete, get, patch, post


class Preference(flask_restful.Resource):
    @requires_auth
    def delete(self):
        return delete('preference',
                      'DELETE FROM preference WHERE id = %(iid)s',
                      {'iid': 1})

    @requires_auth
    def get(self):
        return get('preference',
                   'SELECT * FROM preference WHERE id = %(iid)s',
                   {'iid': 1})

    @requires_auth
    def patch(self):
        """{"json": {"cards": "(bool, default=None)",
                     "info": "(bool, default=None)",
                     "newfeed": "(bool, default=None)",
                     "facebook": "(bool, default=None)",
                     "twitter": "(bool, default=None)",
                     "reposts": "(bool, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('cards', type=bool, location='json', default=None)
        req.add_argument('info', type=bool, location='json', default=None)
        req.add_argument('newsfeed', type=bool, location='json', default=None)

        req.add_argument('facebook', type=bool, location='json', default=None)
        req.add_argument('twitter', type=bool, location='json', default=None)
        req.add_argument('reposts', type=bool, location='json', default=None)
        args = req.parse_args()

        body, stat = get('preference',
                         'SELECT * FROM preference WHERE id = %(iid)s',
                         {'iid': 1})
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            if v is not None:
                item[k] = v

        return patch('preference',
                     """ UPDATE preference
                         SET (cards, info, newsfeed, facebook, twitter,
                              reposts, endtime) =
                             (%(cards)s, %(info)s, %(newsfeed)s, %(facebook)s,
                              %(twitter)s, %(reposts)s)
                         WHERE id = %(id)s """,
                     item)

    @requires_auth
    def post(self):
        """{"json": {"cards": "(bool, default=True)",
                     "info": "(bool, default=True)",
                     "newsfeed": "(bool, default=True)",
                     "facebook": "(bool, default=True)",
                     "twitter": "(bool, default=True)",
                     "reposts": "(bool, default=True)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('cards', type=bool, location='json', default=True)
        req.add_argument('info', type=bool, location='json', default=True)
        req.add_argument('newsfeed', type=bool, location='json', default=True)

        req.add_argument('facebook', type=bool, location='json', default=True)
        req.add_argument('twitter', type=bool, location='json', default=True)
        req.add_argument('reposts', type=bool, location='json', default=True)
        args = req.parse_args()

        return post('preference',
                    """ INSERT INTO preference (cards, info, newsfeed,
                                                facebook, twitter, reposts)
                        VALUES (%(cards)s, %(info)s, %(newsfeed)s,
                                %(facebook)s, %(twitter)s, %(reposts)s)
                        RETURNING id """,
                    args)
