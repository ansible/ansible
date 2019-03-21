# -*- coding: utf-8 -*-

# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url, basic_auth_header

# Makes all classes defined in the file into new-style classes without explicitly inheriting from object
__metaclass__ = type


class BitbucketHelper:
    BITBUCKET_API_URL = 'https://api.bitbucket.org'

    error_messages = {
        'required_client_id': '`client_id` must be specified as a parameter or '
                              'BITBUCKET_CLIENT_ID environment variable',
        'required_client_secret': '`client_secret` must be specified as a parameter or '
                                  'BITBUCKET_CLIENT_SECRET environment variable',
    }

    def __init__(self, module):
        self.module = module
        self.access_token = None

    @staticmethod
    def bitbucket_argument_spec():
        return dict(
            client_id=dict(type='str', no_log=True, fallback=(env_fallback, ['BITBUCKET_CLIENT_ID'])),
            client_secret=dict(type='str', no_log=True, fallback=(env_fallback, ['BITBUCKET_CLIENT_SECRET'])),
        )

    def check_arguments(self):
        if self.module.params['client_id'] is None:
            self.module.fail_json(msg=self.error_messages['required_client_id'])

        if self.module.params['client_secret'] is None:
            self.module.fail_json(msg=self.error_messages['required_client_secret'])

    def fetch_access_token(self):
        self.check_arguments()

        headers = {
            'Authorization': basic_auth_header(self.module.params['client_id'], self.module.params['client_secret'])
        }

        info, content = self.request(
            api_url='https://bitbucket.org/site/oauth2/access_token',
            method='POST',
            data='grant_type=client_credentials',
            headers=headers,
        )

        if info['status'] == 200:
            self.access_token = content['access_token']
        else:
            self.module.fail_json(msg='Failed to retrieve access token: {0}'.format(info))

    def request(self, api_url, method, data=None, headers=None):
        headers = headers or {}

        if self.access_token:
            headers.update({
                'Authorization': 'Bearer {0}'.format(self.access_token),
            })

        if isinstance(data, dict):
            data = self.module.jsonify(data)
            headers.update({
                'Content-type': 'application/json',
            })

        response, info = fetch_url(
            module=self.module,
            url=api_url,
            method=method,
            headers=headers,
            data=data,
            force=True,
        )

        content = {}

        if response is not None:
            body = to_text(response.read())
            if body:
                content = json.loads(body)

        return info, content
