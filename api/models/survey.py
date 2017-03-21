# pylint: disable=R0201
import flask_api
import flask_restful
import flask_restful.reqparse

from api.auth import requires_admin, requires_auth
from api.database import delete, get, gets, patch, post


class SurveyList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('survey', 'SELECT * FROM survey')

    @requires_auth
    @requires_admin
    def post(self):
        """{"json": {"name": "(str, default='')",
                     "description": "(str, default='')",
                     "link": "(str, required)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default='')
        req.add_argument('description', type=str, location='json', default='')
        req.add_argument('link', type=str, location='json', required=True)
        args = req.parse_args()

        return post('survey',
                    """ INSERT INTO survey (name, description, link)
                        VALUES (%(name)s, %(description)s, %(link)s)
                        RETURNING id """,
                    args)


class Survey(flask_restful.Resource):
    @requires_auth
    @requires_admin
    def delete(self, sid):
        return delete('survey',
                      'DELETE FROM survey WHERE id = %(sid)s',
                      {'sid': sid})

    @requires_auth
    def get(self, sid):
        return get('survey',
                   'SELECT * FROM survey WHERE id = %(sid)s',
                   {'sid': sid})

    @requires_auth
    @requires_admin
    def patch(self, sid):
        """{"json": {"name": "(str, default=None)",
                     "description": "(str, default=None)",
                     "link": "(str, default=None)"}}"""
        req = flask_restful.reqparse.RequestParser()
        req.add_argument('name', type=str, location='json', default=None)
        req.add_argument('description', type=str, location='json',
                         default=None)
        req.add_argument('link', type=str, location='json', default=None)
        args = req.parse_args()
        args = {k: v for k, v in args.items() if v is not None}

        body, stat = self.get(sid)
        if stat != flask_api.status.HTTP_200_OK:
            return body, stat

        item = body['data']['attributes']
        for k, v in args.items():
            item[k] = v

        return patch('survey',
                     """ UPDATE survey
                         SET (name, description, link) =
                             (%(name)s, %(description)s, %(link)s)
                         WHERE id = %(id)s """,
                     item)
