# (c) 2018, Victor Fauth <fauthvictor(at)gmail(dot)com>
# (c) 2018, Caio Tedim <caiotedim(at)gmail(dot)com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
author:
    - Victor Fauth (@vfauth)
    - Caio Tedim <caiotedim(at)gmail(dot)com>
lookup: etcd3
short_description: Get data from a etcd3 server
description:
    - Retrieves data from a etcd3 server.
    - Returns a list containing all values whose key has the requested key as a prefix.
version_added: "2.8"
options:
    _raw:
        description:
            - Prefix(es) to look for on etcd.
        type: string
        required: True
    url:
        description:
            - The URL of the etcd3 server.
        default: '127.0.0.1:2379'
        type: string
    user:
        description:
            - The etcd user to authenticate with.
            - Required if I(password) is defined.
    password:
        description:
            - The password to use for authentication.
            - Required if I(user) is defined.
    ca_cert:
        description:
            - The Certificate Authority to use to verify the etcd host.
            - Required if I(client_cert) and I(client_key) are defined.
    client_cert:
        description:
            - PEM formatted certificate chain file to be used for SSL client authentication.
            - Required if I(client_key) is defined.
    client_key:
        description:
            - PEM formatted file that contains your private key to be used for SSL client authentication.
            - Required if I(client_cert) is defined.
    timeout:
        description:
            - The socket level timeout in seconds.
response:
    - Return a list containing values.
    - If no key matched, returns an empty list.
'''

EXAMPLES = '''
    - name: "Get all keys prefixed by 'some_prefix'"
      debug: msg="{{ lookup('etcd3', 'some_prefix', url='127.0.0.1:2379') }}"

    - name: "Get all keys prefixed by 'some_prefix' using a TLS secure connection"
      debug: msg="{{ lookup('etcd3', 'some_prefix', url='127.0.0.1:2379', ca_cert='ca_file.crt') }}"

    - name: "Get all keys prefixed by 'some_prefix' or by 'some_other_prefix' and authenticate using a password"
      debug: msg="{{ lookup('etcd3', 'some_prefix', 'some_other_prefix', url='127.0.0.1:2379', user='someone', password='password123') }}"
'''

RETURN = '''
    _raw:
        description: Data requested as a list containing values.
'''


import json

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.module_utils._text import to_native

try:
    import etcd3
    HAS_ETCD3 = True
except ImportError as e:
    raise AnsibleError("python-etcd3 is required for etcd3 lookup, see https://pypi.org/project/etcd3/")


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        values = []
        try:
            for term in terms:
                params = {}
                params['url'] = kwargs.get('url', '127.0.0.1:2379')
                params['user'] = kwargs.get('user', None)
                params['password'] = kwargs.get('password', None)
                params['ca_cert'] = kwargs.get('ca_cert', None)
                params['cert_cert'] = kwargs.get('client_cert', None)
                params['cert_key'] = kwargs.get('client_key', None)
                params['timeout'] = kwargs.get('timeout', None)

                try:
                    url = params['url'].split(':')
                    params['host'] = url[0]
                    params['port'] = url[1]
                except Exception as e:
                    raise AnsibleError("URL not valid. Error was %s" % to_native(e))

                client_params = {}
                allowed_keys = ['host', 'port', 'user', 'password', 'ca_cert', 'cert_cert', 'cert_key', 'timeout']
                # TODO: Move this back to a dict comprehension when python 2.7 is the minimum supported version
                # client_params = {key: value for key, value in module.params.items() if key in allowed_keys}
                for key, value in params.items():
                    if key in allowed_keys and value is not None:
                        client_params[key] = value

                try:
                    etcd_api = etcd3.client(**client_params)
                except Exception as e:
                    raise AnsibleError("Could not connect to etcd. Error was %s" % to_native(e))

                for value, x in etcd_api.get_prefix(term):
                    if value is not None:
                        values.append(value)

        except Exception as e:
            raise AnsibleError("Error locating '%s' in etcd. Error was %s" % (term, to_native(e)))

        return values
