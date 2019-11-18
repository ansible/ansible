# -*- coding:utf-8 -*-

# Copyright (c) 2019, Piolink Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

import base64
import syslog
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import missing_required_lib

CMD_SITE_TYPE = 'site'
CMD_APP_TYPE = 'app'
CMD_AMSS_TYPE = 'amss'


class PrestModule(object):
    def __init__(self, module):
        self.headers = {'Authorization': '',
                        'Content-Type': ''}

        if not HAS_REQUESTS:
            module.fail_json(msg=missing_required_lib('requests'))

    def basic_auth(self, username, password):
        return "Basic %s" % base64.b64encode(to_bytes(
            "%s:%s" % (username, password), errors='surrogate_or_strict'))

    def set_headers(self, username, password):
        self.headers['Authorization'] = self.basic_auth(username, password)
        self.headers['Content-Type'] = 'application/json'

    def get(self, url):
        return requests.get(url, headers=self.headers, verify=False)

    def post(self, url, data):
        return requests.post(url, headers=self.headers,
                             json=data, verify=False)

    def put(self, url, data):
        return requests.put(url, headers=self.headers, json=data, verify=False)

    def delete(self, url, data):
        return requests.delete(url, headers=self.headers,
                               json=data, verify=False)
