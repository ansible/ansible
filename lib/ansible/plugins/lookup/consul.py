#!/usr/bin/python

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
        description:
          - The C(key) to retrieve from consul K/V Stroe when C(api='kv')
          - The C(name of the service) to fetch info on from Consul when C(api='health_of_service')
          - The C(health state) to filter for when using C(api='health_by_state').
            Can be one of C(any, unknown, passing, warning, critical)
        type: string
        required: True
      api:
        description:
            - Which consul api to use. See (U https://python-consul.readthedocs.io/en/latest/#consul) for an overview.
        type: string
        required: true
        choices:
          - health_of_service
          - health_by_state
          - kv
      recurse:
        type: boolean
        description:
          - If true, will retrieve all the values that have the given key as prefix.
          - Only relevant for C(api='kv')
        default: False
      short_keys:
        type: boolean
        description:
          - When using C(api='kv') and C(recurse=True) then this option will shorten the keys in the result
            in the result by the key you where querying. i.e if your were recursively querying for C(foo/bar)
            this prefix will be removed from every results Key Attribute. C(foo/bar/version) will become C(version).
        default: False
      index:
        description:
          - If the key has a value with the specified index then this is returned allowing access to historical values.
        type: string
      token:
        description:
          - The Consul ACL token to allow access to restricted values.
        env:
          - name: ANSIBLE_CONSUL_ACL_TOKEN
        ini:
          - section: lookup_consul
            key: token
        type: string
      host:
        default: localhost
        description:
          - The target to connect to, must be a resolvable address.
            Will fall back C(ANSIBLE_CONSUL_HOST) if that is set.
          - "C(ANSIBLE_CONSUL_HOST) should look like this: C(my.consul.server)"
        env:
          - name: ANSIBLE_CONSUL_HOST
        ini:
          - section: lookup_consul
            key: host
      port:
        description:
          - The port of the target host to connect to.
            Will fall back to C(ANSIBLE_CONSUL_PORT) if that is set.
        env:
          - name: ANSIBLE_CONSUL_PORT
        ini:
          - section: lookup_consul
            key: port
        default: 8500
        type: int
      scheme:
        description:
          - Whether to use http or https.
            Will fall back to C(ANSIBLE_CONSUL_SCHEME) if set
        env:
          - name: ANSIBLE_CONSUL_SCHEME
        ini:
          - section: lookup_consul
            key: scheme
        default: http
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

EXAMPLES = """
    - name: Retrieve a KV from a Consul at localhost at 8500
      set_fact:
        key_value: "{{ lookup('consul', 'foo/bar', api='kv') }}"

    - name: Retrieve a list of critical services
      set_fact:
        critical_services: "{{ lookup('consul', 'critical', api='health_by_state') }}"

    - name: Retrieve health info about a certain service
      set_fact:
        my_service: "{{ lookup('consul', 'my_service', api='health_of_service') }}"
"""

RETURN = """"
single_kv_result:
    description: A single value of a quried key
    type: string

recurse_kv_result:
    description: A list of kv results
    type: list
    sample:
        - |
          {
            "CreateIndex": 1539295,
            "Flags": 0,
            "Key": "foo/bar",
            "LockIndex": 0,
            "ModifyIndex": 1539295,
            "Value": "BAR_Value"
          }

health_by_state:
    description: A list of nodes with the given health status
    type: list
    sample:
        - |
          {
            "CheckID": "serfHealth",
            "CreateIndex": 1654898,
            "Definition": {},
            "ModifyIndex": 1654898,
            "Name": "Serf Health Status",
            "Node": "nodeFQDN",
            "Notes": "",
            "Output": "Agent alive and reachable",
            "ServiceID": "",
            "ServiceName": "",
            "ServiceTags": [],
            "Status": "passing"
          }

health_of_service_result:
    description: A list of health states of a service
    type: complex
    contains:
        Checks:
            description: A list of checks for the service
            type: list
            sample:
                - |
                  {
                    "CheckID": "serfHealth",
                    "CreateIndex": 1654898,
                    "Definition": {},
                    "ModifyIndex": 1654898,
                    "Name": "Serf Health Status",
                    "Node": "nodeFQDN",
                    "Notes": "",
                    "Output": "Agent alive and reachable",
                    "ServiceID": "",
                    "ServiceName": "",
                    "ServiceTags": [],
                    "Status": "passing"
                  }
        Node:
            description: The node information
            type: complex
            contains:
                Address:
                    description: The IP Address of the Node
                    type: string
                CreateIndex:
                    description: The index of the entry
                    type: int
                Datacenter:
                    description: The name of the datacenter
                    type: string
                ID:
                    description: The node ID
                    type: string
                Meta:
                    description: META Information
                    type: complex
                    contains:
                        consul-network-segment:
                            description: The name of the network segment
                            type: string
                ModifyIndex:
                    description: The modify index ID
                    type: int
                Node:
                    description: The node name
                    type: string
                TaggedAddresses:
                    type: complex
                    contains:
                        lan:
                            description: LAN IP Address
                            type: string
                        wan:
                            description: WAN IP Address
                            type: string
        Service:
            description: Information about the service
            type: complex
            contains:
                Address:
                    description: the address of the service
                    type: string
                Connect:
                    description: information about the connection of the service
                    type: complex
                    contains:
                        Native:
                            description: Is the connection native?
                            type: bool
                        Proxy:
                            description: Information about the proxy if one is used in the connection
                            type: string
                CreateIndex:
                    description: The index of the entry
                    type: int
                EnableTagOverride:
                    description: can tags be overridden
                    type: bool
                ID:
                    description: The ID of the service
                    type: string
                ModifyIndex:
                    description: The modify index ID
                    type: int
                Port:
                    description: The port of the service
                    type: int
                ProxyDestination:
                    description: The proxy destination
                    type: string
                Service:
                    description: The name of the service
                    type: string
                Tags:
                    description: A list of tags associated with the service
                    type: list
                Weights:
                    type: complex
                    contains:
                        Passing:
                            type: int
                        Warning:
                            type: int
"""

import string
import os
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text

try:
    import consul

    HAS_CONSUL = True
except ImportError as importError:
    HAS_CONSUL = False


class LookupModule(LookupBase):
    def _get_value(self, kwargs, key, env_key, default):
        """
        Method to check for values that have eventual fallback values in the os environment
        :param kwargs: The kwargs from the lookup
        :param key: The config key
        :param env_key: The environment key
        :param default: The default fallback
        :return: Either the value from the lookup call or the value from the environment or an default
        """
        if kwargs.get(key) is not None:
            return kwargs.get(key)
        else:
            try:
                return os.environ[env_key]
            except KeyError:
                return default

    def run(self, terms, variables=None, **kwargs):
        if not HAS_CONSUL:
            raise AnsibleError(
                'python-consul is required for consul lookup. See https://python-consul.readthedocs.io/en/latest/#installation')
        api_type = kwargs.get('api')
        if api_type is None:
            raise AnsibleError('You need to define a consul api to use.')

        term = next(iter(terms), None)
        index = kwargs.get('index', None)
        token = kwargs.get('token', None)
        short_keys = kwargs.get('short_keys', False)
        recurse = kwargs.get('recurse', False)
        port = self._get_value(kwargs, 'port', 'ANSIBLE_CONSUL_PORT', 8500)
        hostname = self._get_value(kwargs, 'host', 'ANSIBLE_CONSUL_HOST', 'localhost')
        scheme = self._get_value(kwargs, 'scheme', 'ANSIBLE_CONSUL_SCHEME', 'http')
        validate_certs = self._get_value(kwargs, 'validate_certs', 'ANSIBLE_CONSUL_VALIDATE_CERTS', True)
        client_cert = self._get_value(kwargs, 'client_cert', 'ANSIBLE_CONSUL_CLIENT_CERT', None)

        try:
            consul_api = consul.Consul(host=hostname, port=port, scheme=scheme, verify=validate_certs, cert=client_cert)
            if api_type is 'health_of_service':
                index, results = consul_api.health.service(service=term, token=token, index=index, wait="10s")
                return results
            if api_type is 'health_by_state':
                index, results = consul_api.health.state(name=term, token=token, index=index, wait="10s")
                return results
            elif api_type is 'kv':
                values = []
                index, results = consul_api.kv.get(key=term, token=token, index=index, recurse=recurse, wait="10s")
                if results is not None:
                    if isinstance(results, list):
                        if len(results) == 1:
                            result = next(iter(results))
                            values.append(to_text(result['Value']))
                        else:
                            for result in results:
                                if short_keys:
                                    result['Key'] = string.replace(result['Key'], term + '/', '')
                                values.append(result)
                    elif not isinstance(results, list):
                        values.append(to_text(results['Value']))
                return values
        except Exception as e:
            raise AnsibleError("Error looking up '%s' in consul '%s'. Error was %s" % (term, api_type, e))
