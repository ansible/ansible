#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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

DOCUMENTATION = '''
---
module: bigip_gtm_facts
short_description: Collect facts from F5 BIG-IP GTM devices.
description:
  - Collect facts from F5 BIG-IP GTM devices.
version_added: "2.3"
options:
  include:
    description:
      - Fact category to collect
    required: true
    choices:
      - pool
      - wide_ip
      - virtual_server
  filter:
    description:
      - Perform regex filter of response. Filtering is done on the name of
        the resource. Valid filters are anything that can be provided to
        Python's C(re) module.
    required: false
    default: None
notes:
   - Requires the f5-sdk Python package on the host. This is as easy as
     pip install f5-sdk
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Get pool facts
  bigip_gtm_facts:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      include: "pool"
      filter: "my_pool"
  delegate_to: localhost
'''

RETURN = '''
wide_ip:
    description:
        Contains the lb method for the wide ip and the pools
        that are within the wide ip.
    returned: changed
    type: dict
    sample:
        wide_ip:
            - enabled: "True"
              failure_rcode: "noerror"
              failure_rcode_response: "disabled"
              failure_rcode_ttl: "0"
              full_path: "/Common/foo.ok.com"
              last_resort_pool: ""
              minimal_response: "enabled"
              name: "foo.ok.com"
              partition: "Common"
              persist_cidr_ipv4: "32"
              persist_cidr_ipv6: "128"
              persistence: "disabled"
              pool_lb_mode: "round-robin"
              pools:
                  - name: "d3qw"
                    order: "0"
                    partition: "Common"
                    ratio: "1"
              ttl_persistence: "3600"
              type: "naptr"
pool:
    description: Contains the pool object status and enabled status.
    returned: changed
    type: dict
    sample:
        pool:
            - alternate_mode: "round-robin"
              dynamic_ratio: "disabled"
              enabled: "True"
              fallback_mode: "return-to-dns"
              full_path: "/Common/d3qw"
              load_balancing_mode: "round-robin"
              manual_resume: "disabled"
              max_answers_returned: "1"
              members:
                  - disabled: "True"
                    flags: "a"
                    full_path: "ok3.com"
                    member_order: "0"
                    name: "ok3.com"
                    order: "10"
                    preference: "10"
                    ratio: "1"
                    service: "80"
              name: "d3qw"
              partition: "Common"
              qos_hit_ratio: "5"
              qos_hops: "0"
              qos_kilobytes_second: "3"
              qos_lcs: "30"
              qos_packet_rate: "1"
              qos_rtt: "50"
              qos_topology: "0"
              qos_vs_capacity: "0"
              qos_vs_score: "0"
              ttl: "30"
              type: "naptr"
              verify_member_availability: "disabled"
virtual_server:
    description:
        Contains the virtual server enabled and availability
        status, and address
    returned: changed
    type: dict
    sample:
        virtual_server:
            - addresses:
                  - device_name: "/Common/qweqwe"
                    name: "10.10.10.10"
                    translation: "none"
              datacenter: "/Common/xfxgh"
              enabled: "True"
              expose_route_domains: "no"
              full_path: "/Common/qweqwe"
              iq_allow_path: "yes"
              iq_allow_service_check: "yes"
              iq_allow_snmp: "yes"
              limit_cpu_usage: "0"
              limit_cpu_usage_status: "disabled"
              limit_max_bps: "0"
              limit_max_bps_status: "disabled"
              limit_max_connections: "0"
              limit_max_connections_status: "disabled"
              limit_max_pps: "0"
              limit_max_pps_status: "disabled"
              limit_mem_avail: "0"
              limit_mem_avail_status: "disabled"
              link_discovery: "disabled"
              monitor: "/Common/bigip "
              name: "qweqwe"
              partition: "Common"
              product: "single-bigip"
              virtual_server_discovery: "disabled"
              virtual_servers:
                  - destination: "10.10.10.10:0"
                    enabled: "True"
                    full_path: "jsdfhsd"
                    limit_max_bps: "0"
                    limit_max_bps_status: "disabled"
                    limit_max_connections: "0"
                    limit_max_connections_status: "disabled"
                    limit_max_pps: "0"
                    limit_max_pps_status: "disabled"
                    name: "jsdfhsd"
                    translation_address: "none"
                    translation_port: "0"
'''

try:
    from distutils.version import LooseVersion
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError

    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

import re


class BigIpGtmFactsCommon(object):
    def __init__(self):
        self.api = None
        self.attributes_to_remove = [
            'kind', 'generation', 'selfLink', '_meta_data',
            'membersReference', 'datacenterReference',
            'virtualServersReference', 'nameReference'
        ]
        self.gtm_types = dict(
            a_s='a',
            aaaas='aaaa',
            cnames='cname',
            mxs='mx',
            naptrs='naptr',
            srvs='srv'
        )
        self.request_params = dict(
            params='expandSubcollections=true'
        )

    def is_version_less_than_12(self):
        version = self.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
            return True
        else:
            return False

    def format_string_facts(self, parameters):
        result = dict()
        for attribute in self.attributes_to_remove:
            parameters.pop(attribute, None)
        for key, val in parameters.iteritems():
            result[key] = str(val)
        return result

    def filter_matches_name(self, name):
        if not self.params['filter']:
            return True
        matches = re.match(self.params['filter'], str(name))
        if matches:
            return True
        else:
            return False

    def get_facts_from_collection(self, collection, collection_type=None):
        results = []
        for item in collection:
            if not self.filter_matches_name(item.name):
                continue
            facts = self.format_facts(item, collection_type)
            results.append(facts)
        return results

    def connect_to_bigip(self, **kwargs):
        return ManagementRoot(kwargs['server'],
                              kwargs['user'],
                              kwargs['password'],
                              port=kwargs['server_port'])


class BigIpGtmFactsPools(BigIpGtmFactsCommon):
    def __init__(self, *args, **kwargs):
        super(BigIpGtmFactsPools, self).__init__()
        self.params = kwargs

    def get_facts(self):
        self.api = self.connect_to_bigip(**self.params)
        return self.get_facts_from_device()

    def get_facts_from_device(self):
        try:
            if self.is_version_less_than_12():
                return self.get_facts_without_types()
            else:
                return self.get_facts_with_types()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def get_facts_with_types(self):
        result = []
        for key, type in self.gtm_types.iteritems():
            facts = self.get_all_facts_by_type(key, type)
            if facts:
                result.append(facts)
        return result

    def get_facts_without_types(self):
        pools = self.api.tm.gtm.pools.get_collection(**self.request_params)
        return self.get_facts_from_collection(pools)

    def get_all_facts_by_type(self, key, type):
        collection = getattr(self.api.tm.gtm.pools, key)
        pools = collection.get_collection(**self.request_params)
        return self.get_facts_from_collection(pools, type)

    def format_facts(self, pool, collection_type):
        result = dict()
        pool_dict = pool.to_dict()
        result.update(self.format_string_facts(pool_dict))
        result.update(self.format_member_facts(pool))
        if collection_type:
            result['type'] = collection_type
        return camel_dict_to_snake_dict(result)

    def format_member_facts(self, pool):
        result = []
        if not 'items' in pool.membersReference:
            return dict(members=[])
        for member in pool.membersReference['items']:
            member_facts = self.format_string_facts(member)
            result.append(member_facts)
        return dict(members=result)


class BigIpGtmFactsWideIps(BigIpGtmFactsCommon):
    def __init__(self, *args, **kwargs):
        super(BigIpGtmFactsWideIps, self).__init__()
        self.params = kwargs

    def get_facts(self):
        self.api = self.connect_to_bigip(**self.params)
        return self.get_facts_from_device()

    def get_facts_from_device(self):
        try:
            if self.is_version_less_than_12():
                return self.get_facts_without_types()
            else:
                return self.get_facts_with_types()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def get_facts_with_types(self):
        result = []
        for key, type in self.gtm_types.iteritems():
            facts = self.get_all_facts_by_type(key, type)
            if facts:
                result.append(facts)
        return result

    def get_facts_without_types(self):
        wideips = self.api.tm.gtm.wideips.get_collection(
            **self.request_params
        )
        return self.get_facts_from_collection(wideips)

    def get_all_facts_by_type(self, key, type):
        collection = getattr(self.api.tm.gtm.wideips, key)
        wideips = collection.get_collection(**self.request_params)
        return self.get_facts_from_collection(wideips, type)

    def format_facts(self, wideip, collection_type):
        result = dict()
        wideip_dict = wideip.to_dict()
        result.update(self.format_string_facts(wideip_dict))
        result.update(self.format_pool_facts(wideip))
        if collection_type:
            result['type'] = collection_type
        return camel_dict_to_snake_dict(result)

    def format_pool_facts(self, wideip):
        result = []
        if not hasattr(wideip, 'pools'):
            return dict(pools=[])
        for pool in wideip.pools:
            pool_facts = self.format_string_facts(pool)
            result.append(pool_facts)
        return dict(pools=result)


class BigIpGtmFactsVirtualServers(BigIpGtmFactsCommon):
    def __init__(self, *args, **kwargs):
        super(BigIpGtmFactsVirtualServers, self).__init__()
        self.params = kwargs

    def get_facts(self):
        try:
            self.api = self.connect_to_bigip(**self.params)
            return self.get_facts_from_device()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def get_facts_from_device(self):
        servers = self.api.tm.gtm.servers.get_collection(
            **self.request_params
        )
        return self.get_facts_from_collection(servers)

    def format_facts(self, server, collection_type=None):
        result = dict()
        server_dict = server.to_dict()
        result.update(self.format_string_facts(server_dict))
        result.update(self.format_address_facts(server))
        result.update(self.format_virtual_server_facts(server))
        return camel_dict_to_snake_dict(result)

    def format_address_facts(self, server):
        result = []
        if not hasattr(server, 'addresses'):
            return dict(addresses=[])
        for address in server.addresses:
            address_facts = self.format_string_facts(address)
            result.append(address_facts)
        return dict(addresses=result)

    def format_virtual_server_facts(self, server):
        result = []
        if not 'items' in server.virtualServersReference:
            return dict(virtual_servers=[])
        for server in server.virtualServersReference['items']:
            server_facts = self.format_string_facts(server)
            result.append(server_facts)
        return dict(virtual_servers=result)

class BigIpGtmFactsManager(object):
    def __init__(self, *args, **kwargs):
        self.params = kwargs
        self.api = None

    def get_facts(self):
        result = dict()
        facts = dict()

        if 'pool' in self.params['include']:
            facts['pool'] = self.get_pool_facts()
        if 'wide_ip' in self.params['include']:
            facts['wide_ip'] = self.get_wide_ip_facts()
        if 'virtual_server' in self.params['include']:
            facts['virtual_server'] = self.get_virtual_server_facts()

        result.update(**facts)
        result.update(dict(changed=True))
        return result

    def get_pool_facts(self):
        pools = BigIpGtmFactsPools(**self.params)
        return pools.get_facts()

    def get_wide_ip_facts(self):
        wide_ips = BigIpGtmFactsWideIps(**self.params)
        return wide_ips.get_facts()

    def get_virtual_server_facts(self):
        wide_ips = BigIpGtmFactsVirtualServers(**self.params)
        return wide_ips.get_facts()


class BigIpGtmFactsModuleConfig(object):
    def __init__(self):
        self.argument_spec = dict()
        self.meta_args = dict()
        self.supports_check_mode = False
        self.valid_includes = ['pool', 'wide_ip', 'virtual_server']
        self.initialize_meta_args()
        self.initialize_argument_spec()

    def initialize_meta_args(self):
        args = dict(
            include=dict(type='list', required=True),
            filter=dict(type='str', required=False)
        )
        self.meta_args = args

    def initialize_argument_spec(self):
        self.argument_spec = f5_argument_spec()
        self.argument_spec.update(self.meta_args)

    def create(self):
        return AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=self.supports_check_mode
        )


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    config = BigIpGtmFactsModuleConfig()
    module = config.create()

    try:
        obj = BigIpGtmFactsManager(
            check_mode=module.check_mode, **module.params
        )
        result = obj.get_facts()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
