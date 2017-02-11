import collections
import json
import os

import flask
from flask import _request_ctx_stack
import flask_api
import flask_restful

import api.auth
import api.models.broadcast
import api.models.event
import api.models.info
import api.models.preference
import api.models.social
import api.models.subscription
import api.models.user


SECRET_KEY = os.environ.get('SECRET_KEY', '[not-a-s3cr3t]')


app = flask.Flask(__name__)
app.secret_key = SECRET_KEY
app.url_map.strict_slashes = False


restful = flask_restful.Api(app, prefix='/api')
restful.add_resource(api.models.broadcast.Broadcast, '/broadcast/<int:bid>')
restful.add_resource(api.models.broadcast.BroadcastList, '/broadcast')

restful.add_resource(api.models.event.Event, '/event/<int:eid>')
restful.add_resource(api.models.event.EventList, '/event')
restful.add_resource(api.models.event.EventUserList,
                     '/event/subscribed/<uid>',
                     '/user/<uid>/subscribed')

restful.add_resource(api.models.info.Info, '/info')

restful.add_resource(api.models.preference.Preference, '/preference')

restful.add_resource(api.models.social.SocialContentList, '/social')
restful.add_resource(api.models.social.SocialContentUploadURL,
                     '/social-image-upload-url')
restful.add_resource(api.models.social.SingleSocialContent,
                     '/social/<float:postid>')
restful.add_resource(api.models.social.SingleSocialContentLikes,
                     '/social/<float:postid>/likes')

restful.add_resource(api.models.subscription.Subscription,
                     '/user/<uid>/subscription/<int:eid>',
                     '/event/<int:eid>/subscription/<uid>')
restful.add_resource(api.models.subscription.SubscriptionEventList,
                     '/event/<int:eid>/subscription')
restful.add_resource(api.models.subscription.SubscriptionUserList,
                     '/user/<uid>/subscription')

restful.add_resource(api.models.user.User, '/user/<uid>')
restful.add_resource(api.models.user.UserList, '/user')
restful.add_resource(api.models.user.UserPhoto, '/user/<uid>/photo')


@app.route('/api')
def spec():
    data = {'meta': dict()}
    for rule in flask.current_app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue

        methods = sorted([m for m in rule.methods
                          if m not in ('HEAD', 'OPTIONS')])
        methods = collections.OrderedDict.fromkeys(methods)

        for method in methods:
            try:
                cls = app.view_functions[rule.endpoint].view_class
            except AttributeError:
                continue

            fn = getattr(cls, method.lower())
            try:
                methods[method] = json.loads(fn.__doc__ or {})
            except Exception:
                pass

        data['meta'][rule.rule] = methods

    return flask.jsonify(data), flask_api.status.HTTP_200_OK


@app.route('/api/me')
def me():
    # This needs to be wrapped since `current_user` is only valid in a
    # `@requires_auth` context.
    @api.auth.requires_auth
    def get_current_user():
        user = _request_ctx_stack.top.current_user
        return user, flask_api.status.HTTP_200_OK

    user, code = get_current_user()
    data = {'data': {'id': user['sub'], 'type': 'user'}}
    return flask.jsonify(data), code


@app.route('/api/ping')
def ping():
    return 'pong'


@app.after_request
def cors(response):
    response.headers['Access-Control-Allow-Headers'] = ', '.join(
        ('Authorization', 'Content-Type'))
    response.headers['Access-Control-Allow-Methods'] = ', '.join(
        ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
