import collections
import json
import logging
import os
import sys

import flask
from flask import _request_ctx_stack
import flask_api
import flask_restful
from raven.contrib.flask import Sentry

import api.auth
import api.models.broadcast
import api.models.card
import api.models.conference
import api.models.contact
import api.models.event
import api.models.info
import api.models.location
import api.models.preference
import api.models.social
import api.models.sponsor
import api.models.stream
import api.models.subscription
import api.models.survey
import api.models.user


SECRET_KEY = os.environ.get('SECRET_KEY', '[not-a-s3cr3t]')


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


app = flask.Flask(__name__)
app.secret_key = SECRET_KEY
app.url_map.strict_slashes = False
sentry = Sentry(app, logging=True, level=logging.INFO)


restful = flask_restful.Api(app, prefix='/api')
restful.add_resource(api.models.broadcast.Broadcast, '/broadcast/<int:bid>')
restful.add_resource(api.models.broadcast.BroadcastList, '/broadcast')

restful.add_resource(api.models.conference.ConferenceList, '/conference')

restful.add_resource(api.models.event.Event, '/event/<int:eid>')
restful.add_resource(api.models.event.EventList, '/event')
restful.add_resource(api.models.event.EventUserList,
                     '/event/subscribed/<uid>',
                     '/user/<uid>/subscribed')

restful.add_resource(api.models.info.Info, '/info')
restful.add_resource(api.models.card.Card, '/info/card/<int:cid>')
restful.add_resource(api.models.card.CardList, '/info/card')
restful.add_resource(api.models.contact.Contact, '/info/contact/<int:cid>')
restful.add_resource(api.models.contact.ContactList, '/info/contact')
restful.add_resource(api.models.location.Location, '/info/location/<int:lid>')
restful.add_resource(api.models.location.LocationList, '/info/location')
restful.add_resource(api.models.sponsor.Sponsor, '/info/sponsor/<int:sid>')
restful.add_resource(api.models.sponsor.SponsorList, '/info/sponsor')

restful.add_resource(api.models.preference.Preference, '/preference')

restful.add_resource(api.models.social.SocialContentList, '/social')
restful.add_resource(api.models.social.FlaggedPostList, '/social/flags')
restful.add_resource(api.models.social.SocialContentUploadURL,
                     '/social-image-upload-url')
restful.add_resource(api.models.social.SingleSocialContent,
                     '/social/<float:postid>')
restful.add_resource(api.models.social.SingleSocialContentLikes,
                     '/social/<float:postid>/likes')
restful.add_resource(api.models.social.PostFlag,
                     '/social/<float:postid>/flag')
restful.add_resource(api.models.social.AdminUnflagPost,
                     '/social/<float:postid>/unflag')

restful.add_resource(api.models.stream.StreamList, '/stream')

restful.add_resource(api.models.subscription.Subscription,
                     '/user/<uid>/subscription/<int:eid>',
                     '/event/<int:eid>/subscription/<uid>')
restful.add_resource(api.models.subscription.SubscriptionEventList,
                     '/event/<int:eid>/subscription')
restful.add_resource(api.models.subscription.SubscriptionUserList,
                     '/user/<uid>/subscription')

restful.add_resource(api.models.survey.Survey, '/survey/<int:sid>')
restful.add_resource(api.models.survey.SurveyList, '/survey')

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
