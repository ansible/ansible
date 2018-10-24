# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url


def online_argument_spec():
    return dict(
        api_token=dict(required=True, fallback=(env_fallback, ['ONLINE_TOKEN', 'ONLINE_API_KEY', 'ONLINE_OAUTH_TOKEN', 'ONLINE_API_TOKEN']),
                       no_log=True, aliases=['oauth_token']),
        api_url=dict(fallback=(env_fallback, ['ONLINE_API_URL']), default='https://api.online.net', aliases=['base_url']),
        api_timeout=dict(type='int', default=30, aliases=['timeout']),
        validate_certs=dict(default=True, type='bool'),
    )


class OnlineException(Exception):

    def __init__(self, message):
        self.message = message


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]

    @property
    def ok(self):
        return self.status_code in (200, 201, 202, 204)


class Online(object):

    def __init__(self, module):
        self.module = module
        self.headers = {
            'Authorization': "Bearer %s" % self.module.params.get('api_token'),
            'User-Agent': self.get_user_agent_string(module),
            'Content-type': 'application/json',
        }
        self.name = None

    def get_resources(self):
        results = self.get('/%s' % self.name)
        if not results.ok:
            raise OnlineException('Error fetching {0} ({1}) [{2}: {3}]'.format(
                self.name, '%s/%s' % (self.module.params.get('api_url'), self.name),
                results.status_code, results.json['message']
            ))

        return results.json

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.module.params.get('api_url'), path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        if headers is not None:
            self.headers.update(headers)

        resp, info = fetch_url(
            self.module, url, data=data, headers=self.headers, method=method,
            timeout=self.module.params.get('api_timeout')
        )

        # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        return Response(resp, info)

    @staticmethod
    def get_user_agent_string(module):
        return "ansible %s Python %s" % (module.ansible_version, sys.version.split(' ')[0])

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)

    def patch(self, path, data=None, headers=None):
        return self.send("PATCH", path, data, headers)

    def update(self, path, data=None, headers=None):
        return self.send("UPDATE", path, data, headers)
