# (c) 2015, Steve Gargan <steve.gargan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: consul_kv
    version_added: "1.9"
    short_description: Fetch  metadata from a Consul key value store.
    description:
      - Lookup metadata for a playbook from the key value store in a Consul cluster.
        Values can be easily set in the kv store with simple rest commands
      - C(curl -X PUT -d 'some-value' http://localhost:8500/v1/kv/ansible/somedata)
    requirements:
      - 'python-consul python library U(http://python-consul.readthedocs.org/en/latest/#installation)'
    options:
      _raw:
        description: List of key(s) to retrieve.
        type: list
        required: True
      recurse:
        type: boolean
        description: If true, will retrieve all the values that have the given key as prefix.
        default: False
      index:
        description: If the key has a value with the specified index then this is returned allowing access to historical values.
      token:
        description: The acl token to allow access to restricted values.
      host:
        default: localhost
        description:
           - The target to connect to, must be a resolvable address.
        env:
          - name: ANSIBLE_CONSUL_URL
      port:
        description: The port of the target host to connect to.
        default: 8500
"""

EXAMPLES = """
  - debug:
      msg: 'key contains {{item}}'
    with_consul_kv:
      - 'key/to/retrieve'

  - name: Parameters can be provided after the key be more specific about what to retrieve
    debug:
      msg: 'key contains {{item}}'
    with_consul_kv:
      - 'key/to recurse=true token=E6C060A9-26FB-407A-B83E-12DDAFCB4D98'

  - name: retrieving a KV from a remote cluster on non default port
    debug:
      msg: "{{ lookup('consul_kv', 'my/key', host='10.10.10.10', port='2000') }}"
"""

RETURN = """
  _raw:
    description:
      - Value(s) stored in consul.
"""

import os
import sys
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.plugins.lookup import LookupBase

try:
    import json
except ImportError:
    import simplejson as json

try:
    import consul
    HAS_CONSUL = True
except ImportError as e:
    HAS_CONSUL = False


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        if not HAS_CONSUL:
            raise AnsibleError('python-consul is required for consul_kv lookup. see http://python-consul.readthedocs.org/en/latest/#installation')

        values = []
        try:
            for term in terms:
                params = self.parse_params(term)
                try:
                    url = os.environ['ANSIBLE_CONSUL_URL']
                    u = urlparse(url)
                    consul_api = consul.Consul(host=u.hostname, port=u.port, scheme=u.scheme)
                except KeyError:
                    port = kwargs.get('port', '8500')
                    host = kwargs.get('host', 'localhost')
                    consul_api = consul.Consul(host=host, port=port)

                results = consul_api.kv.get(params['key'],
                                            token=params['token'],
                                            index=params['index'],
                                            recurse=params['recurse'])
                if results[1]:
                    # responds with a single or list of result maps
                    if isinstance(results[1], list):
                        for r in results[1]:
                            values.append(r['Value'])
                    else:
                        values.append(results[1]['Value'])
        except Exception as e:
            raise AnsibleError(
                "Error locating '%s' in kv store. Error was %s" % (term, e))

        return values

    def parse_params(self, term):
        params = term.split(' ')

        paramvals = {
            'key': params[0],
            'token': None,
            'recurse': False,
            'index': None
        }

        # parameters specified?
        try:
            for param in params[1:]:
                if param and len(param) > 0:
                    name, value = param.split('=')
                    if name not in paramvals:
                        raise AnsibleAssertionError("%s not a valid consul lookup parameter" % name)
                    paramvals[name] = value
        except (ValueError, AssertionError) as e:
            raise AnsibleError(e)

        return paramvals
