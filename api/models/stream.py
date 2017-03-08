# pylint: disable=R0201
import flask_restful

from api.auth import requires_auth
from api.database import gets


class StreamList(flask_restful.Resource):
    @requires_auth
    def get(self):
        return gets('stream', "SELECT DISTINCT 'foo' as id, stream FROM event")
