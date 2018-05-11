# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
import sys

from ansible.module_utils.urls import open_url, fetch_url
from ansible.module_utils.parsing.convert_bool import BOOLEANS
from ansible.module_utils.six import string_types
from ansible.module_utils.six import iteritems
from ansible.module_utils.urls import urllib_error
from ansible.module_utils._text import to_native
from ansible.module_utils.six import PY3

try:
    import json as _json
except ImportError:
    import simplejson as _json

try:
    from library.module_utils.network.f5.common import F5ModuleError
except ImportError:
    from ansible.module_utils.network.f5.common import F5ModuleError


"""An F5 REST API URI handler.

Use this module to make calls to an F5 REST server. It is influenced by the same
API that the Python ``requests`` tool uses, but the two are not the same, as the
library here is **much** more simple and targeted specifically to F5's needs.

The ``requests`` design was chosen due to familiarity with the tool. Internally,
the classes contained herein use Ansible native libraries.

The means by which you should use it are similar to ``requests`` basic usage.

Authentication is not handled for you automatically by this library, however it *is*
handled automatically for you in the supporting F5 module_utils code; specifically the
different product module_util files (bigip.py, bigiq.py, etc).

Internal (non-module) usage of this library looks like this.

```
# Create a session instance
mgmt = iControlRestSession()
mgmt.verify = False

server = '1.1.1.1'
port = 443

# Payload used for getting an initial authentication token
payload = {
  'username': 'admin',
  'password': 'secret',
  'loginProviderName': 'tmos'
}

# Create URL to call, injecting server and port
url = f"https://{server}:{port}/mgmt/shared/authn/login"

# Call the API
resp = session.post(url, json=payload)

# View the response
print(resp.json())

# Update the session with the authentication token
session.headers['X-F5-Auth-Token'] = resp.json()['token']['token']

# Create another URL to call, injecting server and port
url = f"https://{server}:{port}/mgmt/tm/ltm/virtual/~Common~virtual1"

# Call the API
resp = session.get(url)

# View the details of a virtual payload
print(resp.json())
```
"""


class Request(object):
    def __init__(self, method=None, url=None, headers=None, data=None, params=None,
                 auth=None, json=None):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.data = data or []
        self.json = json
        self.params = params or {}
        self.auth = auth

    def prepare(self):
        p = PreparedRequest()
        p.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            data=self.data,
            json=self.json,
            params=self.params,
        )
        return p


class PreparedRequest(object):
    def __init__(self):
        self.method = None
        self.url = None
        self.headers = None
        self.body = None

    def prepare(self, method=None, url=None, headers=None, data=None, params=None, json=None):
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_body(data, json)

    def prepare_url(self, url, params):
        self.url = url

    def prepare_method(self, method):
        self.method = method
        if self.method:
            self.method = self.method.upper()

    def prepare_headers(self, headers):
        self.headers = {}
        if headers:
            for k, v in iteritems(headers):
                self.headers[k] = v

    def prepare_body(self, data, json=None):
        body = None
        content_type = None

        if not data and json is not None:
            self.headers['Content-Type'] = 'application/json'
            body = _json.dumps(json)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')

        if data:
            body = data
            content_type = None

        if content_type and 'content-type' not in self.headers:
            self.headers['Content-Type'] = content_type

        self.body = body


class Response(object):
    def __init__(self):
        self._content = None
        self.status = None
        self.headers = dict()
        self.url = None
        self.reason = None
        self.request = None

    def json(self):
        return _json.loads(self._content)


class iControlRestSession(object):
    """Represents a session that communicates with a BigIP.

    Instantiate one of these when you want to communicate with an F5 REST
    Server, it will handle F5-specific authentication.

    Pass an existing authentication token to the ``token`` argument to re-use
    that token for authentication. Otherwise, token authentication is handled
    automatically for you.

    On BIG-IQ, it may be necessary to pass the ``auth_provider`` argument if the
    user has a different authentication handler configured. Otherwise, the system
    defaults for the different products will be used.
    """
    def __init__(self):
        self.headers = self.default_headers()
        self.verify = True
        self.params = {}
        self.timeout = 30

        self.server = None
        self.user = None
        self.password = None
        self.server_port = None
        self.auth_provider = None

    def _normalize_headers(self, headers):
        result = {}
        result.update(dict((k.lower(), v) for k, v in headers))

        # Don't be lossy, append header values for duplicate headers
        # In Py2 there is nothing that needs done, py2 does this for us
        if PY3:
            temp_headers = {}
            for name, value in headers:
                # The same as above, lower case keys to match py2 behavior, and create more consistent results
                name = name.lower()
                if name in temp_headers:
                    temp_headers[name] = ', '.join((temp_headers[name], value))
                else:
                    temp_headers[name] = value
            result.update(temp_headers)
        return result

    def default_headers(self):
        return {
            'connection': 'keep-alive',
            'accept': '*/*',
        }

    def prepare_request(self, request):
        headers = self.headers.copy()
        params = self.params.copy()

        if request.headers is not None:
            headers.update(request.headers)
        if request.params is not None:
            params.update(request.params)

        prepared = PreparedRequest()
        prepared.prepare(
            method=request.method,
            url=request.url,
            data=request.data,
            json=request.json,
            headers=headers,
            params=params,
        )
        return prepared

    def request(self, method, url, params=None, data=None, headers=None, auth=None,
                timeout=None, verify=None, json=None):
        request = Request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json,
            data=data or {},
            params=params or {},
            auth=auth
        )
        kwargs = dict(
            timeout=timeout,
            verify=verify
        )
        prepared = self.prepare_request(request)
        return self.send(prepared, **kwargs)

    def send(self, request, **kwargs):
        response = Response()

        params = dict(
            method=request.method,
            data=request.body,
            timeout=kwargs.get('timeout', None) or self.timeout,
            validate_certs=kwargs.get('verify', None) or self.verify,
            headers=request.headers
        )

        try:
            result = open_url(request.url, **params)
            response._content = result.read().decode('utf-8')
            response.status = result.getcode()
            response.url = result.geturl()
            response.msg = "OK (%s bytes)" % result.headers.get('Content-Length', 'unknown')
            response.headers = self._normalize_headers(result.headers.items())
            response.request = request
        except urllib_error.HTTPError as e:
            try:
                response._content = e.read()
            except AttributeError:
                response._content = ''

            response.reason = to_native(e)
            response.status_code = e.code
        return response

    def delete(self, url, json=None, **kwargs):
        return self.request('DELETE', url, json=json, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request('PATCH', url, data=data, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('POST', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request('PUT', url, data=data, **kwargs)


def debug_prepared_request(url, method, headers, data=None):
    result = "curl -k -X {0} {1}".format(method.upper(), url)
    for k, v in iteritems(headers):
        result = result + " -H '{0}: {1}'".format(k, v)
    if any(v == 'application/json' for k, v in iteritems(headers)):
        if data:
            kwargs = _json.loads(data.decode('utf-8'))
            result = result + " -d '" + _json.dumps(kwargs, sort_keys=True) + "'"
    return result
