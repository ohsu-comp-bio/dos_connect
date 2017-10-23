"""
This middleware emits webhook notifications following successful
object creation, deletion, copy or metadata operations.  In its current
incarnation it also requires middleware that will identify a tenant to which
the request refers, but that could be changed.

The notification payload is dependent on the type of event, but always
includes project_id, container, obj. For events other than deletion,
timestamps, content lengths, metadata may be included.

To configure, in proxy-server.conf:

    [filter:webhookmiddleware]
    paste.filter_factory = swift.common.middleware.webhook_notifications:filter_factory

    publisher_id = swift.localhost
    transport_url = http(s)://user:password@host:port/
    notification_driver = messaging
    notification_topics = notifications

Additionally, in pipeline:main, add webhookmiddleware to the pipeline;
it should be added towards the end to ensure any required environment
information is present when it runs.

Finally, webhook needs to be installed with its dependencies.

"""

from datetime import datetime
import logging

import six
from swift.common.swob import HTTPForbidden, HTTPBadRequest, \
            HTTPRequestEntityTooLarge, Request

from swift.common.wsgi import make_env, make_pre_authed_env, \
            make_pre_authed_request

from swift.common import wsgi
from swift.common.utils import get_logger

import requests
import json 


class WebHookContext(wsgi.WSGIContext):
    def __init__(self, app, notifier):
        wsgi.WSGIContext.__init__(self, app)
        self._notifier = notifier
        self.agent = "%(orig)s OsloMessaging"

    def _timestamp_to_str(self, timestamp):
        dt = datetime.fromtimestamp(float(timestamp))
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

    def _get_metadata(self, request_headers, prefix):
        added_prefix = 'X-%s-Meta-' % prefix

        return {k.lower(): v
                for k, v in six.iteritems(request_headers)
                if k.startswith(added_prefix)}

    def _get_object_metadata(self, request_headers, response_headers):
        object_metadata = self._get_metadata(request_headers, 'Object')
        etag_headers = filter(lambda h: h[0] == 'Etag', response_headers)
        if etag_headers:
            object_metadata['etag'] = etag_headers[0][1]
        return object_metadata

    def _get_container_metadata(self, request_headers, response_headers):
        return self._get_metadata(request_headers, 'Container')

    def _get_account_metadata(self, request_headers, response_headers):
        return self._get_metadata(request_headers, 'Account')

    def _get_request_auth_info(self, request_headers):
        return {
                'project_id': request_headers.get('X-Project-Id'),
                'project_name': request_headers.get('X-Project-Name'),
                'project_domain_id': request_headers.get('X-Project-Domain-Id'),
                'project_domain_name': request_headers.get('X-Project-Domain-Name'),
                'x-trans-id': request_headers.get('X-Trans-Id')
        }

    def _make_head_request(self, env):
        tmp_req = make_pre_authed_request(env, method="HEAD")
        resp = tmp_req.get_response(self.app)
        return resp

    def handle_request(self, env, start_response):
        request = Request(env)
        method = request.method
        if method not in ('POST', 'PUT', 'COPY', 'DELETE'):
            return self.app(env, start_response)

        # Get the response from the rest of the pipeline before we
        # start doing anything; this means that whatever is being created
        # or deleted will have been done before we start constructing
        # the notification payload
        response = self._app_call(env)
        status_code = self._get_status_int()

        try:
            ver, account, container, obj = request.split_path(
                2, 4, rest_with_last=True)
        except ValueError:
            start_response(self._response_status,
                           self._response_headers,
                           self._response_exc_info)
            return response

        event_methods = {
            'DELETE': 'delete',
            'COPY': 'copy',
            'PUT': 'create',
            'POST': 'metadata'
        }
        event_object = ('object' if obj
                        else 'container' if container
                        else 'account')

        event_type = '%s.%s' % (event_object, event_methods[method])

        if status_code in (200, 201, 202, 204):
            request_headers = request.headers

            payload = self._get_request_auth_info(request_headers)
            payload['account'] = account
            if container:
                payload['container'] = container
                if obj:
                    payload['object'] = obj

            if method != 'DELETE':
                head_headers = self._make_head_request(env).headers

                copy_from = request_headers.get('X-Copy-From')
                if method == 'PUT' and copy_from:
                    # Copies are turned into PUTs with an X-Copy-From
                    # in the object middleware
                    # though we don't need to handle them differently
                    event_type = event_methods['COPY']
                    if copy_from[0] == '/':
                        copy_from = copy_from[1:]
                    copy_from_container, copy_from_object = copy_from.split('/', 1)

                    payload['copy-from-container'] = copy_from_container
                    payload['copy-from-object'] = copy_from_object

                    if request_headers.get('X-Fresh-Metadata', None):
                        payload['copy-fresh-metadata'] = bool(request_headers.get('X-Fresh-Metadata'))

                payload.update(self._get_account_metadata(request_headers, self._response_headers))
                if container:
                    payload.update(self._get_container_metadata(request_headers, self._response_headers))

                    if obj:
                        payload.update(self._get_object_metadata(request_headers, self._response_headers))

                modified_timestamp = head_headers.get('X-Timestamp')
                if modified_timestamp:
                    modified_datetime = datetime.fromtimestamp(float(modified_timestamp))
                    payload['updated_at'] = modified_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')
                    payload['x-timestamp'] = modified_timestamp

                def set_field_if_exists(source, dest):
                    value = head_headers.get(source)
                    if value:
                        payload[dest] = value

                set_field_if_exists('Last-Modified', 'last-modified')

                if obj:
                    for field in (('Content-Length', 'content-length'),
                                  ('Content-Type', 'content-type')):
                        set_field_if_exists(*field)

            self._notifier.info({}, event_type, payload)

        # We don't want to tamper with the response
        start_response(self._response_status,
                       self._response_headers,
                       self._response_exc_info)

        return response


class LoggingNotifier(object):
    def __init__(self, logger, conf):
        self.logger = logger
        self.conf = conf

    def info(self, obj, event_type, payload):
        try:
            payload['event_type'] = event_type
            self.logger.info('webhook_filter::WebHookMiddleware::LoggingNotifier')
            self.logger.info('event_type:{}'.format(event_type))
            self.logger.info(payload)
            api_url = self.conf.get('api_url',None)
            self.logger.info('api_url:{}'.format(api_url))
            if api_url:
                r = requests.post(api_url, data=json.dumps(payload), headers={"content-type": "application/json"} )
                self.logger.info(r.status_code)
                self.logger.info(r.headers['content-type'])
                self.logger.info(r.content)
        except Exception as e:
            self.logger.error(e)


class WebHookMiddleware(object):
    def __init__(self, app, conf):
        self._app = app
        self.logger = get_logger(conf, log_route='webhook')
        self.logger.info("webhook_filter::WebHookMiddleware")
        self._notifier = LoggingNotifier(self.logger, conf)

    def __call__(self, env, start_response):
        self.logger.info("webhook_filter::WebHookMiddleware.__call__")
        messaging_context = WebHookContext(self._app, self._notifier)
        return messaging_context.handle_request(env, start_response)


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    logger = get_logger(conf, log_route='webhook')
    logger.info("webhook_filter::filter_factory conf: {}".format(conf))

    def webhook_filter(app):
        return WebHookMiddleware(app, conf)
    return webhook_filter

