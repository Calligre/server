import os

import flask
import flask_api
import flask_restful

import api.models.event
import api.models.info
import api.models.subscription
import api.models.user


SECRET_KEY = os.environ.get('SECRET_KEY', '[not-a-s3cr3t]')


app = flask.Flask(__name__)
app.secret_key = SECRET_KEY


restful = flask_restful.Api(app)
restful.add_resource(api.models.event.Event, '/event/<int:eid>')
restful.add_resource(api.models.event.EventList, '/event')
restful.add_resource(api.models.info.Info, '/info')
restful.add_resource(api.models.subscription.Subscription,
                     '/user/<int:uid>/subscription/<int:eid>')
restful.add_resource(api.models.subscription.SubscriptionEventList,
                     '/event/<int:eid>/subscription')
restful.add_resource(api.models.subscription.SubscriptionUserList,
                     '/user/<int:uid>/subscription')
restful.add_resource(api.models.user.User, '/user/<int:uid>')
restful.add_resource(api.models.user.UserList, '/user')


@app.route('/')
def spec():
    data = {'meta': dict()}

    for rule in flask.current_app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        if rule.rule in ('/', '/ping'):
            continue

        data['meta'][rule.rule] = [m for m in rule.methods
                                   if m not in ('HEAD', 'OPTIONS')]

    return flask.jsonify(data), flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/ping')
def ping():
    return 'pong'
