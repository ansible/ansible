# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Ansible Project 2017
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

import json
import os
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback


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
                return json.loads(to_text(self.info["body"]))
            return None
        try:
            return json.loads(to_text(self.body))
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]


class DigitalOceanHelper:

    def __init__(self, module):
        self.module = module
        self.baseurl = 'https://api.digitalocean.com/v2'
        self.timeout = module.params.get('timeout', 30)
        self.oauth_token = module.params.get('oauth_token')
        self.headers = {'Authorization': 'Bearer {0}'.format(self.oauth_token),
                        'Content-type': 'application/json'}

        # Check if api_token is valid or not
        response = self.get('account')
        if response.status_code == 401:
            self.module.fail_json(msg='Failed to login using API token, please verify validity of API token.')

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method, timeout=self.timeout)

        return Response(resp, info)

    def get(self, path, data=None):
        return self.send('GET', path, data)

    def put(self, path, data=None):
        return self.send('PUT', path, data)

    def post(self, path, data=None):
        return self.send('POST', path, data)

    def delete(self, path, data=None):
        return self.send('DELETE', path, data)

    @staticmethod
    def digital_ocean_argument_spec():
        return dict(
            validate_certs=dict(type='bool', required=False, default=True),
            oauth_token=dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN', 'OAUTH_TOKEN']),
                required=False,
                aliases=['api_token'],
            ),
            timeout=dict(type='int', default=30),
        )

    def get_paginated_data(self, base_url=None, data_key_name=None, data_per_page=40, expected_status_code=200):
        """
        Function to get all paginated data from given URL
        Args:
            base_url: Base URL to get data from
            data_key_name: Name of data key value
            data_per_page: Number results per page (Default: 40)
            expected_status_code: Expected returned code from DigitalOcean (Default: 200)
        Returns: List of data

        """
        page = 1
        has_next = True
        ret_data = []
        status_code = None
        response = None
        while has_next or status_code != expected_status_code:
            required_url = "{0}page={1}&per_page={2}".format(base_url, page, data_per_page)
            response = self.get(required_url)
            status_code = response.status_code
            # stop if any error during pagination
            if status_code != expected_status_code:
                break
            page += 1
            ret_data.extend(response.json[data_key_name])
            has_next = "pages" in response.json["links"] and "next" in response.json["links"]["pages"]

        if status_code != expected_status_code:
            msg = "Failed to fetch %s from %s" % (data_key_name, base_url)
            if response:
                msg += " due to error : %s" % response.json['message']
            self.module.fail_json(msg=msg)

        return ret_data
