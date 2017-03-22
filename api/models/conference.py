# pylint: disable=R0201
import flask_restful

from api.database import gets


class ConferenceList(flask_restful.Resource):
    def get(self):
        return gets('conference', 'SELECT * FROM conference')
