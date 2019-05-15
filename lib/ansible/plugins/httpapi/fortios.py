# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2019 Fortinet, Inc
# All rights reserved.
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
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.basic import to_text
import json
import re

class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApiBase, self).__init__()

        self._connection = connection
        self._become = False
        self._become_pass = ''
        self._ccsrftoken = ''

    def set_become(self, become_context):
        self._become = become_context.become
        self._become_pass = getattr(become_context, 'become_pass') or ''

    def login(self, username, password):
        """Call a defined login endpoint to receive an authentication token."""

        data = "username=" + username + "&secretkey=" + password + "&ajax=1"
        status, result_data = self.send_request(url='/logincheck', data=data, method='POST')
        if result_data[0] != '1':
            raise Exception('Wrong credentials. Please check')

    def logout(self):
        """ Call to implement session logout."""

        self.send_request(url='/logout', method="POST")

    def update_auth(self, response, response_text):
        """Return per-request auth token.

        The response should be a dictionary that can be plugged into the
        headers of a request. The default implementation uses cookie data.
        If no authentication data is found, return None
        """

        cookies = {}

        for attr, val in response.getheaders():
            if attr == 'Set-Cookie' and 'APSCOOKIE_' in val:
                cookies['Cookie'] = val

            elif attr == 'Set-Cookie' and 'ccsrftoken=' in val:
                csrftoken_search = re.search('\"(.*)\"', val)
                if csrftoken_search:
                    self._ccsrftoken = csrftoken_search.group(1)

        return cookies

    def handle_httperror(self, exc):
        """Overridable method for dealing with HTTP codes.

        This method will attempt to handle known cases of HTTP status codes.
        If your API uses status codes to convey information in a regular way,
        you can override this method to handle it appropriately.

        :returns:
            * True if the code has been handled in a way that the request
            may be resent without changes.
            * False if the error cannot be handled or recovered from by the
            plugin. This will result in the HTTPError being returned to the
            caller to deal with as appropriate.
            * Any other value returned is taken as a valid response from the
            server without making another request. In many cases, this can just
            be the original exception.
            """
        if exc.code == 401 and self._connection._auth:
            # Stored auth appears to be invalid, clear and retry
            self._connection._auth = None
            self.login(self._connection.get_option('remote_user'), self._connection.get_option('password'))
            return True

        return exc

    def send_request(self, **message_kwargs):
        url = message_kwargs.get('url', '/')
        data = message_kwargs.get('data', '')
        method = message_kwargs.get('method', 'GET')

        if self._ccsrftoken == '' and not (method == 'POST' and 'logincheck' in url):
            raise Exception('Not logged in. Please login first')

        headers = {}
        if self._ccsrftoken != '':
            headers['x-csrftoken'] = self._ccsrftoken

        if method == 'POST' or 'PUT':
            headers['Content-Type'] = 'application/json'

        try:
            response, response_data = self._connection.send(url, data, headers=headers, method=method)

            return response.status, to_text(response_data.getvalue())
        except Exception as err:
            raise Exception(err)
