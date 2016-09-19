import os

import flask
import flask_api
import flask_restful

import api.models.broadcast
import api.models.event
import api.models.info
import api.models.subscription
import api.models.user


SECRET_KEY = os.environ.get('SECRET_KEY', '[not-a-s3cr3t]')


app = flask.Flask(__name__)
app.secret_key = SECRET_KEY


restful = flask_restful.Api(app, prefix='/api')
restful.add_resource(api.models.broadcast.Broadcast, '/broadcast/<int:bid>')
restful.add_resource(api.models.broadcast.BroadcastList, '/broadcast')
restful.add_resource(api.models.event.Event, '/event/<int:eid>')
restful.add_resource(api.models.event.EventList, '/event')
restful.add_resource(api.models.event.EventUserList,
                     '/event/subscribed/<uid>',
                     '/user/<uid>/subscribed')
restful.add_resource(api.models.info.Info, '/info')
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

    # TODO: pull these from Dynamo spec
    data['meta']['/api/content'] = ['GET', 'POST']
    data['meta']['/api/content/<int:cid>'] = ['DELETE', 'GET']

    for rule in flask.current_app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue

        data['meta'][rule.rule] = sorted([m for m in rule.methods
                                          if m not in ('HEAD', 'OPTIONS')])

    return flask.jsonify(data), flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/api/ping')
def ping():
    return 'pong'


@app.after_request
def cors(response):
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = ', '.join(
        ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
