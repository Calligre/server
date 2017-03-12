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
        """{"json": {"newfeed": "(bool, default=None)",
                     "events": "(bool, default=None)",
                     "content": "(bool, default=None)",
                     "contact": "(bool, default=None)",
                     "location": "(bool, default=None)",
                     "map": "(bool, default=None)",
                     "package": "(bool, default=None)",
                     "facebook": "(bool, default=None)",
                     "twitter": "(bool, default=None)",
                     "reposts": "(bool, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('newsfeed', type=bool, location='json', default=None)
        req.add_argument('events', type=bool, location='json', default=None)
        req.add_argument('content', type=bool, location='json', default=None)
        req.add_argument('contact', type=bool, location='json', default=None)

        req.add_argument('location', type=bool, location='json', default=None)
        req.add_argument('map', type=bool, location='json', default=None)
        req.add_argument('package', type=bool, location='json', default=None)

        req.add_argument('facebook', type=bool, location='json', default=None)
        req.add_argument('twitter', type=bool, location='json', default=None)
        req.add_argument('reposts', type=bool, location='json', default=None)
        args = req.parse_args()

        body, stat = self.get()
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            if v is not None:
                item[k] = v

        return patch('preference',
                     """ UPDATE preference
                         SET (newsfeed, events, content, contact, location,
                              map, package, facebook, twitter, reposts) =
                             (%(newsfeed)s, %(events)s, %(content)s,
                              %(contact)s, %(location)s, %(map)s, %(package)s,
                              %(facebook)s, %(twitter)s, %(reposts)s)
                         WHERE id = %(id)s """,
                     item)

    @requires_auth
    def post(self):
        """{"json": {"newsfeed": "(bool, default=True)",
                     "events": "(bool, default=True)",
                     "content": "(bool, default=True)",
                     "contact": "(bool, default=True)",
                     "location": "(bool, default=True)",
                     "map": "(bool, default=True)",
                     "package": "(bool, default=True)",
                     "facebook": "(bool, default=True)",
                     "twitter": "(bool, default=True)",
                     "reposts": "(bool, default=True)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('newsfeed', type=bool, location='json', default=True)
        req.add_argument('events', type=bool, location='json', default=True)
        req.add_argument('content', type=bool, location='json', default=True)
        req.add_argument('contact', type=bool, location='json', default=True)

        req.add_argument('location', type=bool, location='json', default=True)
        req.add_argument('map', type=bool, location='json', default=True)
        req.add_argument('package', type=bool, location='json', default=True)

        req.add_argument('facebook', type=bool, location='json', default=True)
        req.add_argument('twitter', type=bool, location='json', default=True)
        req.add_argument('reposts', type=bool, location='json', default=True)
        args = req.parse_args()

        return post('preference',
                    """ INSERT INTO preference (newsfeed, events, content,
                                                contact, location, map,
                                                package, facebook, twitter,
                                                reposts)
                        VALUES (%(newsfeed)s, %(events)s, %(content)s,
                                %(contact)s, %(location)s, %(map)s,
                                %(package)s, %(facebook)s, %(twitter)s,
                                %(reposts)s)
                        RETURNING id """,
                    args)
