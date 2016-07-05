#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Hiroaki Nakamura <hnakamur@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

try:
    import json
except ImportError:
    import simplejson as json

# httplib/http.client connection using unix domain socket
import socket
import ssl
try:
    from httplib import HTTPConnection, HTTPSConnection
except ImportError:
    # Python 3
    from http.client import HTTPConnection, HTTPSConnection

class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path):
        HTTPConnection.__init__(self, 'localhost')
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock

from ansible.module_utils.urls import generic_urlparse
try:
    from urlparse import urlparse
except ImportError:
    # Python 3
    from url.parse import urlparse

class LXDClientException(Exception):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

class LXDClient(object):
    def __init__(self, url, key_file=None, cert_file=None, debug=False):
        """LXD Client.

        :param url: The URL of the LXD server. (e.g. unix:/var/lib/lxd/unix.socket or https://127.0.0.1)
        :type url: ``str``
        :param key_file: The path of the client certificate key file.
        :type key_file: ``str``
        :param cert_file: The path of the client certificate file.
        :type cert_file: ``str``
        :param debug: The debug flag. The request and response are stored in logs when debug is true.
        :type debug: ``bool``
        """
        self.url = url
        self.debug = debug
        self.logs = []
        if url.startswith('https:'):
            self.cert_file = cert_file
            self.key_file = key_file
            parts = generic_urlparse(urlparse(self.url))
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(cert_file, keyfile=key_file)
            self.connection = HTTPSConnection(parts.get('netloc'), context=ctx)
        elif url.startswith('unix:'):
            unix_socket_path = url[len('unix:'):]
            self.connection = UnixHTTPConnection(unix_socket_path)
        else:
            raise LXDClientException('URL scheme must be unix: or https:')

    def do(self, method, url, body_json=None, ok_error_codes=None, timeout=None):
        resp_json = self._send_request(method, url, body_json=body_json, ok_error_codes=ok_error_codes, timeout=timeout)
        if resp_json['type'] == 'async':
            url = '{0}/wait'.format(resp_json['operation'])
            resp_json = self._send_request('GET', url)
            if resp_json['metadata']['status'] != 'Success':
                self._raise_err_from_json(resp_json)
        return resp_json

    def authenticate(self, trust_password):
        body_json = {'type': 'client', 'password': trust_password}
        return self._send_request('POST', '/1.0/certificates', body_json=body_json)

    def _send_request(self, method, url, body_json=None, ok_error_codes=None, timeout=None):
        try:
            body = json.dumps(body_json)
            self.connection.request(method, url, body=body)
            resp = self.connection.getresponse()
            resp_json = json.loads(resp.read())
            self.logs.append({
                'type': 'sent request',
                'request': {'method': method, 'url': url, 'json': body_json, 'timeout': timeout},
                'response': {'json': resp_json}
            })
            resp_type = resp_json.get('type', None)
            if resp_type == 'error':
                if ok_error_codes is not None and resp_json['error_code'] in ok_error_codes:
                    return resp_json
                self._raise_err_from_json(resp_json)
            return resp_json
        except socket.error as e:
            raise LXDClientException('cannot connect to the LXD server', err=e)

    def _raise_err_from_json(self, resp_json):
        err_params = {}
        if self.debug:
            err_params['logs'] = self.logs
        raise LXDClientException(self._get_err_from_resp_json(resp_json), **err_params)

    @staticmethod
    def _get_err_from_resp_json(resp_json):
        err = None
        metadata = resp_json.get('metadata', None)
        if metadata is not None:
            err = metadata.get('err', None)
        if err is None:
            err = resp_json.get('error', None)
        return err
