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


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author:
    - Miguel Angel Munoz (@magonzalez)
httpapi : fortios
short_description: HttpApi Plugin for Fortinet FortiOS Appliance or VM
description:
  - This HttpApi plugin provides methods to connect to Fortinet FortiOS Appliance or VM via REST API
version_added: "2.9"
"""

from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.basic import to_text
from ansible.module_utils.six.moves import urllib
import json
import re


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)

        self._ccsrftoken = ''

    def set_become(self, become_context):
        """
        Elevation is not required on Fortinet devices - Skipped
        :param become_context: Unused input.
        :return: None
        """
        return None

    def login(self, username, password):
        """Call a defined login endpoint to receive an authentication token."""

        data = "username=" + urllib.parse.quote(username) + "&secretkey=" + urllib.parse.quote(password) + "&ajax=1"
        dummy, result_data = self.send_request(url='/logincheck', data=data, method='POST')
        if result_data[0] != '1':
            raise Exception('Wrong credentials. Please check')

    def logout(self):
        """ Call to implement session logout."""

        self.send_request(url='/logout', method="POST")

    def update_auth(self, response, response_text):
        """
        Get cookies and obtain value for csrftoken that will be used on next requests
        :param response: Response given by the server.
        :param response_text Unused_input.
        :return: Dictionary containing headers
        """

        headers = {}
        resp_raw_headers = []
        if hasattr(response.headers, '_headers'):
            resp_raw_headers = response.headers._headers
        else:
            resp_raw_headers = [(attr, response.headers[attr]) for attr in response.headers]
        for attr, val in resp_raw_headers:
            if attr.lower() == 'set-cookie' and 'APSCOOKIE_' in val:
                headers['Cookie'] = val
                # XXX: In urllib2 all the 'set-cookie' headers are coalesced into one
                x_ccsrftoken_position = val.find('ccsrftoken=')
                if x_ccsrftoken_position != -1:
                    token_string = val[x_ccsrftoken_position + len('ccsrftoken='):].split('\"')[1]
                    self._ccsrftoken = token_string

            elif attr.lower() == 'set-cookie' and 'ccsrftoken=' in val:
                csrftoken_search = re.search('\"(.*)\"', val)
                if csrftoken_search:
                    self._ccsrftoken = csrftoken_search.group(1)

        headers['x-csrftoken'] = self._ccsrftoken

        return headers

    def handle_httperror(self, exc):
        """
        Not required on Fortinet devices - Skipped
        :param exc: Unused input.
        :return: exc
        """
        return exc

    def send_request(self, **message_kwargs):
        """
        Responsible for actual sending of data to the connection httpapi base plugin.
        :param message_kwargs: A formatted dictionary containing request info: url, data, method

        :return: Status code and response data.
        """
        url = message_kwargs.get('url', '/')
        data = message_kwargs.get('data', '')
        method = message_kwargs.get('method', 'GET')

        try:
            response, response_data = self.connection.send(url, data, method=method)
            response_status = None
            if hasattr(response, 'status'):
                response_status = response.status
            else:
                response_status = response.headers.status
            return response_status, to_text(response_data.getvalue())
        except Exception as err:
            raise Exception(err)
