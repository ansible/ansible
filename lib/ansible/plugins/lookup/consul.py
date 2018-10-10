# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
    lookup: consul
    version_added: "2.7"
    short_description: Fetch data from a Consul server or cluster
    description:
      - Wrapper for the python-consul library
    requirements:
      - 'python-consul python library U(https://python-consul.readthedocs.io/en/latest/#installation)'
    options:
      _raw:
        description: key to retrieve from consul
        type: string
        required: True
      api:
        description:
            - Which consul api to use. See (U https://python-consul.readthedocs.io/en/latest/#consul) for an overview.
        type: string
        required: true
        choices:
          - health_service
          - health_state
          - kv
      recurse:
        type: boolean
        description:
          - If true, will retrieve all the values that have the given key as prefix.
          - Only relevant for C(api='kv')
        default: False
      index:
        description:
          - If the key has a value with the specified index then this is returned allowing access to historical values.
        type: string
      token:
        description: The acl token to allow access to restricted values.
        type: string
      host:
        default: localhost
        description:
          - The target to connect to, must be a resolvable address.
            Will be determined from C(ANSIBLE_CONSUL_URL) if that is set.
          - "C(ANSIBLE_CONSUL_URL) should look like this: C(https://my.consul.server:8500)"
        env:
          - name: ANSIBLE_CONSUL_URL
        ini:
          - section: lookup_consul
            key: host
      port:
        description:
          - The port of the target host to connect to.
          - If you use C(ANSIBLE_CONSUL_URL) this value will be used from there.
        default: 8500
      scheme:
        default: http
        description:
          - Whether to use http or https.
          - If you use C(ANSIBLE_CONSUL_URL) this value will be used from there.
        type: string
      validate_certs:
        default: True
        description: Whether to verify the ssl connection or not.
        env:
          - name: ANSIBLE_CONSUL_VALIDATE_CERTS
        ini:
          - section: lookup_consul
            key: validate_certs
      client_cert:
        default: None
        description: The client cert to verify the ssl connection.
        env:
          - name: ANSIBLE_CONSUL_CLIENT_CERT
        ini:
          - section: lookup_consul
            key: client_cert
"""
import string
import os
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible.errors import AnsibleError

from ansible.plugins.lookup import LookupBase

try:
    import consul

    HAS_CONSUL = True
except ImportError as importError:
    HAS_CONSUL = False


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_CONSUL:
            raise AnsibleError(
                'python-consul is required for consul lookup. See https://python-consul.readthedocs.io/en/latest/#installation')
        if kwargs.get('api') is None:
            raise AnsibleError('You need to define a consul api to use.')
        key = next(iter(terms), None)
        index = kwargs.get('index', None)
        token = kwargs.get('token', None)
        short_keys = kwargs.get('short_keys', False)
        recurse = kwargs.get('recurse', False)
        try:
            url = os.environ['ANSIBLE_CONSUL_URL']
            validate_certs = os.environ['ANSIBLE_CONSUL_VALIDATE_CERTS'] or True
            client_cert = os.environ['ANSIBLE_CONSUL_CLIENT_CERT'] or None
            scheme, hostname, port = urlparse(url)
        except KeyError:
            port = kwargs.get('port', '8500')
            hostname = kwargs.get('host', 'localhost')
            scheme = kwargs.get('scheme', 'http')
            validate_certs = kwargs.get('validate_certs', True)
            client_cert = kwargs.get('client_cert', None)

        try:
            consul_api = consul.Consul(host=hostname, port=port, scheme=scheme, verify=validate_certs, cert=client_cert)
            results = None
            if kwargs.get('api') is 'health_service':
                index, results = consul_api.health.service(key, token=token, index=index)
            if kwargs.get('api') is 'health_state':
                index, results = consul_api.health.state(key, token=token, index=index)
            elif kwargs.get('api') is 'kv':
                index, results = consul_api.kv.get(key, token=token, index=index, recurse=recurse)
                if results is not None:
                    if isinstance(results, list) and short_keys:
                        for result in results:
                            result['Key'] = string.replace(result['Key'], key + '/', '')

            return results
        except Exception as e:
            raise AnsibleError("Error looking up '%s' in consul '%s'. Error was %s" % (key, kwargs.get('api'), e))
