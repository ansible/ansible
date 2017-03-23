# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
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
'''
DOCUMENTATION:
    author:
        - Jan-Piet Mens (@jpmens)
    lookup: etcd
    version_added: "2.1"
    short_description: get info from etcd server
    description:
        - Retrieves data from an etcd server
    options:
        _raw:
            description:
                - the list of keys to lookup on the etcd server
            type: list
            element_type: string
            required: True
        _etcd_url:
            description:
                - Environment variable with the url for the etcd server
            default: 'http://127.0.0.1:4001'
            env_vars:
                - name: ANSIBLE_ETCD_URL
        _etcd_version:
            description:
                - Environment variable with the etcd protocol version
            default: 'v1'
            env_vars:
                - name: ANSIBLE_ETCD_VERSION
EXAMPLES:
    - name: "a value from a locally running etcd"
      debug: msg={{ lookup('etcd', 'foo') }}
RETURN:
    _list:
        description:
            - list of values associated with input keys
        type: strings
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

try:
    import json
except ImportError:
    import simplejson as json

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url

# this can be made configurable, not should not use ansible.cfg
ANSIBLE_ETCD_URL = 'http://127.0.0.1:4001'
if os.getenv('ANSIBLE_ETCD_URL') is not None:
    ANSIBLE_ETCD_URL = os.environ['ANSIBLE_ETCD_URL']

ANSIBLE_ETCD_VERSION = 'v1'
if os.getenv('ANSIBLE_ETCD_VERSION') is not None:
    ANSIBLE_ETCD_VERSION = os.environ['ANSIBLE_ETCD_VERSION']

class Etcd:
    def __init__(self, url=ANSIBLE_ETCD_URL, version=ANSIBLE_ETCD_VERSION,
                 validate_certs=True):
        self.url = url
        self.version = version
        self.baseurl = '%s/%s/keys' % (self.url,self.version)
        self.validate_certs = validate_certs

    def get(self, key):
        url = "%s/%s" % (self.baseurl, key)

        data = None
        value = ""
        try:
            r = open_url(url, validate_certs=self.validate_certs)
            data = r.read()
        except:
            return value

        try:
            # {"action":"get","key":"/name","value":"Jane Jolie","index":5}
            item = json.loads(data)
            if self.version == 'v1':
                if 'value' in item:
                    value = item['value']
            else:
                if 'node' in item:
                    value = item['node']['value']

            if 'errorCode' in item:
                value = "ENOENT"
        except:
            raise
            pass

        return value

class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        validate_certs = kwargs.get('validate_certs', True)

        etcd = Etcd(validate_certs=validate_certs)

        ret = []
        for term in terms:
            key = term.split()[0]
            value = etcd.get(key)
            ret.append(value)
        return ret
