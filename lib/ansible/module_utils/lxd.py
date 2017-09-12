# -*- coding: utf-8 -*-

# (c) 2016, Hiroaki Nakamura <hnakamur@gmail.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import socket
import ssl

from ansible.module_utils.urls import generic_urlparse
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils.six.moves import http_client
from ansible.module_utils._text import to_text

# httplib/http.client connection using unix domain socket
HTTPConnection = http_client.HTTPConnection
HTTPSConnection = http_client.HTTPSConnection

try:
    import json
except ImportError:
    import simplejson as json


class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path):
        HTTPConnection.__init__(self, 'localhost')
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock


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
            resp_data = resp.read()
            resp_data = to_text(resp_data, errors='surrogate_or_strict')
            resp_json = json.loads(resp_data)
            self.logs.append({
                'type': 'sent request',
                'request': {'method': method, 'url': url, 'json': body_json, 'timeout': timeout},
                'response': {'json': resp_json}
            })
            resp_type = resp_json.get('type', None)
            if resp_type == 'error':
                if ok_error_codes is not None and resp_json['error_code'] in ok_error_codes:
                    return resp_json
                if resp_json['error'] == "Certificate already in trust store":
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
