# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
# (m) 2016, Mihai Moldovanu <mihaim@tfm.ro>
# (m) 2017, Juan Manuel Parrilla <jparrill@redhat.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author:
        - Jan-Piet Mens (@jpmens)
    lookup: etcd
    version_added: "2.1"
    short_description: get info from an etcd server
    description:
        - Retrieves data from an etcd server
    options:
        _terms:
            description:
                - the list of keys to lookup on the etcd server
            type: list
            elements: string
            required: True
        url:
            description:
                - Environment variable with the url for the etcd server
            default: 'http://127.0.0.1:4001'
            env:
              - name: ANSIBLE_ETCD_URL
        version:
            description:
                - Environment variable with the etcd protocol version
            default: 'v1'
            env:
              - name: ANSIBLE_ETCD_VERSION
        validate_certs:
            description:
                - toggle checking that the ssl certificates are valid, you normally only want to turn this off with self-signed certs.
            default: True
            type: boolean
'''

EXAMPLES = '''
    - name: "a value from a locally running etcd"
      debug: msg={{ lookup('etcd', 'foo/bar') }}

    - name: "values from multiple folders on a locally running etcd"
      debug: msg={{ lookup('etcd', 'foo', 'bar', 'baz') }}

    - name: "since Ansible 2.5 you can set server options inline"
      debug: msg="{{ lookup('etcd', 'foo', version='v2', url='http://192.168.0.27:4001') }}"
'''

RETURN = '''
    _raw:
        description:
            - list of values associated with input keys
        type: list
        elements: strings
'''

import json

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url

# this can be made configurable, not should not use ansible.cfg
#
# Made module configurable from playbooks:
# If etcd  v2 running on host 192.168.1.21 on port 2379
# we can use the following in a playbook to retrieve /tfm/network/config key
#
# - debug: msg={{lookup('etcd','/tfm/network/config', url='http://192.168.1.21:2379' , version='v2')}}
#
# Example Output:
#
# TASK [debug] *******************************************************************
# ok: [localhost] => {
#     "msg": {
#         "Backend": {
#             "Type": "vxlan"
#         },
#         "Network": "172.30.0.0/16",
#         "SubnetLen": 24
#     }
# }
#
#
#
#


class Etcd:
    def __init__(self, url, version, validate_certs):
        self.url = url
        self.version = version
        self.baseurl = '%s/%s/keys' % (self.url, self.version)
        self.validate_certs = validate_certs

    def _parse_node(self, node):
        # This function will receive all etcd tree,
        # if the level requested has any node, the recursion starts
        # create a list in the dir variable and it is passed to the
        # recursive function, and so on, if we get a variable,
        # the function will create a key-value at this level and
        # undoing the loop.
        path = {}
        if node.get('dir', False):
            for n in node.get('nodes', []):
                path[n['key'].split('/')[-1]] = self._parse_node(n)

        else:
            path = node['value']

        return path

    def get(self, key):
        url = "%s/%s?recursive=true" % (self.baseurl, key)
        data = None
        value = {}
        try:
            r = open_url(url, validate_certs=self.validate_certs)
            data = r.read()
        except Exception:
            return None

        try:
            # I will not support Version 1 of etcd for folder parsing
            item = json.loads(data)
            if self.version == 'v1':
                # When ETCD are working with just v1
                if 'value' in item:
                    value = item['value']
            else:
                if 'node' in item:
                    # When a usual result from ETCD
                    value = self._parse_node(item['node'])

            if 'errorCode' in item:
                # Here return an error when an unknown entry responds
                value = "ENOENT"
        except Exception:
            raise

        return value


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        validate_certs = self.get_option('validate_certs')
        url = self.get_option('url')
        version = self.get_option('version')

        etcd = Etcd(url=url, version=version, validate_certs=validate_certs)

        ret = []
        for term in terms:
            key = term.split()[0]
            value = etcd.get(key)
            ret.append(value)
        return ret
