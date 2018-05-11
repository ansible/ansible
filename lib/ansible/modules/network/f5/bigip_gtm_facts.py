#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_gtm_facts
short_description: Collect facts from F5 BIG-IP GTM devices
description:
  - Collect facts from F5 BIG-IP GTM devices.
version_added: 2.3
options:
  include:
    description:
      - Fact category to collect.
    required: True
    choices:
      - pool
      - wide_ip
      - server
  filter:
    description:
      - Perform regex filter of response. Filtering is done on the name of
        the resource. Valid filters are anything that can be provided to
        Python's C(re) module.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Get pool facts
  bigip_gtm_facts:
    server: lb.mydomain.com
    user: admin
    password: secret
    include: pool
    filter: my_pool
  delegate_to: localhost
'''

RETURN = r'''
wide_ip:
  description:
    Contains the lb method for the wide ip and the pools that are within the wide ip.
  returned: changed
  type: list
  sample:
    wide_ip:
      - enabled: True
        failure_rcode: noerror
        failure_rcode_response: disabled
        failure_rcode_ttl: 0
        full_path: /Common/foo.ok.com
        last_resort_pool: ""
        minimal_response: enabled
        name: foo.ok.com
        partition: Common
        persist_cidr_ipv4: 32
        persist_cidr_ipv6: 128
        persistence: disabled
        pool_lb_mode: round-robin
        pools:
          - name: d3qw
            order: 0
            partition: Common
            ratio: 1
        ttl_persistence: 3600
        type: naptr
pool:
  description: Contains the pool object status and enabled status.
  returned: changed
  type: list
  sample:
    pool:
      - alternate_mode: round-robin
        dynamic_ratio: disabled
        enabled: True
        fallback_mode: return-to-dns
        full_path: /Common/d3qw
        load_balancing_mode: round-robin
        manual_resume: disabled
        max_answers_returned: 1
        members:
          - disabled: True
            flags: a
            full_path: ok3.com
            member_order: 0
            name: ok3.com
            order: 10
            preference: 10
            ratio: 1
            service: 80
        name: d3qw
        partition: Common
        qos_hit_ratio: 5
        qos_hops: 0
        qos_kilobytes_second: 3
        qos_lcs: 30
        qos_packet_rate: 1
        qos_rtt: 50
        qos_topology: 0
        qos_vs_capacity: 0
        qos_vs_score: 0
        availability_state: offline
        enabled_state: disabled
        ttl: 30
        type: naptr
        verify_member_availability: disabled
server:
  description:
    Contains the virtual server enabled and availability status, and address.
  returned: changed
  type: list
  sample:
    server:
      - addresses:
          - device_name: /Common/qweqwe
            name: 10.10.10.10
            translation: none
        datacenter: /Common/xfxgh
        enabled: True
        expose_route_domains: no
        full_path: /Common/qweqwe
        iq_allow_path: yes
        iq_allow_service_check: yes
        iq_allow_snmp: yes
        limit_cpu_usage: 0
        limit_cpu_usage_status: disabled
        limit_max_bps: 0
        limit_max_bps_status: disabled
        limit_max_connections: 0
        limit_max_connections_status: disabled
        limit_max_pps: 0
        limit_max_pps_status: disabled
        limit_mem_avail: 0
        limit_mem_avail_status: disabled
        link_discovery: disabled
        monitor: /Common/bigip
        name: qweqwe
        partition: Common
        product: single-bigip
        virtual_server_discovery: disabled
        virtual_servers:
          - destination: 10.10.10.10:0
            enabled: True
            full_path: jsdfhsd
            limit_max_bps: 0
            limit_max_bps_status: disabled
            limit_max_connections: 0
            limit_max_connections_status: disabled
            limit_max_pps: 0
            limit_max_pps_status: disabled
            name: jsdfhsd
            translation_address: none
            translation_port: 0
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.utils.responses.handlers import Stats
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.utils.responses.handlers import Stats
    except ImportError:
        HAS_F5SDK = False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

        self.types = dict(
            a_s='a',
            aaaas='aaaa',
            cnames='cname',
            mxs='mx',
            naptrs='naptr',
            srvs='srv'
        )

    def filter_matches_name(self, name):
        if self.want.filter is None:
            return True
        matches = re.match(self.want.filter, str(name))
        if matches:
            return True
        else:
            return False

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
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

    def read_stats_from_device(self, resource):
        stats = Stats(resource.stats.load())
        return stats.stat


class UntypedManager(BaseManager):
    def exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            filtered = [(k, v) for k, v in iteritems(attrs) if self.filter_matches_name(k)]
            if filtered:
                results.append(dict(filtered))
        return results


class TypedManager(BaseManager):
    def exec_module(self):
        results = []
        for collection, type in iteritems(self.types):
            facts = self.read_facts(collection)
            if not facts:
                continue
            for x in facts:
                x.update({'type': type})
            for item in facts:
                attrs = item.to_return()
                filtered = [(k, v) for k, v in iteritems(attrs) if self.filter_matches_name(k)]
                if filtered:
                    results.append(dict(filtered))
        return results


class Parameters(AnsibleF5Parameters):
    @property
    def include(self):
        requested = self._values['include']
        valid = ['pool', 'wide_ip', 'server', 'all']

        if any(x for x in requested if x not in valid):
            raise F5ModuleError(
                "The valid 'include' choices are {0}".format(', '.join(valid))
            )

        if 'all' in requested:
            return ['all']
        else:
            return requested


class BaseParameters(Parameters):
    @property
    def enabled(self):
        if self._values['enabled'] is None:
            return None
        elif self._values['enabled'] in BOOLEANS_TRUE:
            return True
        else:
            return False

    @property
    def disabled(self):
        if self._values['disabled'] is None:
            return None
        elif self._values['disabled'] in BOOLEANS_TRUE:
            return True
        else:
            return False

    def _remove_internal_keywords(self, resource):
        resource.pop('kind', None)
        resource.pop('generation', None)
        resource.pop('selfLink', None)
        resource.pop('isSubcollection', None)
        resource.pop('fullPath', None)

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class PoolParameters(BaseParameters):
    api_map = {
        'alternateMode': 'alternate_mode',
        'dynamicRatio': 'dynamic_ratio',
        'fallbackMode': 'fallback_mode',
        'fullPath': 'full_path',
        'loadBalancingMode': 'load_balancing_mode',
        'manualResume': 'manual_resume',
        'maxAnswersReturned': 'max_answers_returned',
        'qosHitRatio': 'qos_hit_ratio',
        'qosHops': 'qos_hops',
        'qosKilobytesSecond': 'qos_kilobytes_second',
        'qosLcs': 'qos_lcs',
        'qosPacketRate': 'qos_packet_rate',
        'qosRtt': 'qos_rtt',
        'qosTopology': 'qos_topology',
        'qosVsCapacity': 'qos_vs_capacity',
        'qosVsScore': 'qos_vs_score',
        'verifyMemberAvailability': 'verify_member_availability',
        'membersReference': 'members'
    }

    returnables = [
        'alternate_mode', 'dynamic_ratio', 'enabled', 'disabled', 'fallback_mode',
        'load_balancing_mode', 'manual_resume', 'max_answers_returned', 'members',
        'name', 'partition', 'qos_hit_ratio', 'qos_hops', 'qos_kilobytes_second',
        'qos_lcs', 'qos_packet_rate', 'qos_rtt', 'qos_topology', 'qos_vs_capacity',
        'qos_vs_score', 'ttl', 'type', 'full_path', 'availability_state',
        'enabled_state', 'availability_status'
    ]

    @property
    def max_answers_returned(self):
        if self._values['max_answers_returned'] is None:
            return None
        return int(self._values['max_answers_returned'])

    @property
    def members(self):
        result = []
        if self._values['members'] is None or 'items' not in self._values['members']:
            return result
        for item in self._values['members']['items']:
            self._remove_internal_keywords(item)
            if 'disabled' in item:
                if item['disabled'] in BOOLEANS_TRUE:
                    item['disabled'] = True
                else:
                    item['disabled'] = False
            if 'enabled' in item:
                if item['enabled'] in BOOLEANS_TRUE:
                    item['enabled'] = True
                else:
                    item['enabled'] = False
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            if 'memberOrder' in item:
                item['member_order'] = int(item.pop('memberOrder'))
            # Cast some attributes to integer
            for x in ['order', 'preference', 'ratio', 'service']:
                if x in item:
                    item[x] = int(item[x])
            result.append(item)
        return result

    @property
    def qos_hit_ratio(self):
        if self._values['qos_hit_ratio'] is None:
            return None
        return int(self._values['qos_hit_ratio'])

    @property
    def qos_hops(self):
        if self._values['qos_hops'] is None:
            return None
        return int(self._values['qos_hops'])

    @property
    def qos_kilobytes_second(self):
        if self._values['qos_kilobytes_second'] is None:
            return None
        return int(self._values['qos_kilobytes_second'])

    @property
    def qos_lcs(self):
        if self._values['qos_lcs'] is None:
            return None
        return int(self._values['qos_lcs'])

    @property
    def qos_packet_rate(self):
        if self._values['qos_packet_rate'] is None:
            return None
        return int(self._values['qos_packet_rate'])

    @property
    def qos_rtt(self):
        if self._values['qos_rtt'] is None:
            return None
        return int(self._values['qos_rtt'])

    @property
    def qos_topology(self):
        if self._values['qos_topology'] is None:
            return None
        return int(self._values['qos_topology'])

    @property
    def qos_vs_capacity(self):
        if self._values['qos_vs_capacity'] is None:
            return None
        return int(self._values['qos_vs_capacity'])

    @property
    def qos_vs_score(self):
        if self._values['qos_vs_score'] is None:
            return None
        return int(self._values['qos_vs_score'])

    @property
    def availability_state(self):
        if self._values['stats'] is None:
            return None
        try:
            result = self._values['stats']['status_availabilityState']
            return result['description']
        except AttributeError:
            return None

    @property
    def enabled_state(self):
        if self._values['stats'] is None:
            return None
        try:
            result = self._values['stats']['status_enabledState']
            return result['description']
        except AttributeError:
            return None

    @property
    def availability_status(self):
        # This fact is a combination of the availability_state and enabled_state
        #
        # The purpose of the fact is to give a higher-level view of the availability
        # of the pool, that can be used in playbooks. If you need further detail,
        # consider using the following facts together.
        #
        # - availability_state
        # - enabled_state
        #
        if self.enabled_state == 'enabled':
            if self.availability_state == 'offline':
                return 'red'
            elif self.availability_state == 'available':
                return 'green'
            elif self.availability_state == 'unknown':
                return 'blue'
            else:
                return 'none'
        else:
            # disabled
            return 'black'


class WideIpParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'failureRcode': 'failure_return_code',
        'failureRcodeResponse': 'failure_return_code_response',
        'failureRcodeTtl': 'failure_return_code_ttl',
        'lastResortPool': 'last_resort_pool',
        'minimalResponse': 'minimal_response',
        'persistCidrIpv4': 'persist_cidr_ipv4',
        'persistCidrIpv6': 'persist_cidr_ipv6',
        'poolLbMode': 'pool_lb_mode',
        'ttlPersistence': 'ttl_persistence'
    }

    returnables = [
        'full_path', 'description', 'enabled', 'disabled', 'failure_return_code',
        'failure_return_code_response', 'failure_return_code_ttl', 'last_resort_pool',
        'minimal_response', 'persist_cidr_ipv4', 'persist_cidr_ipv6', 'pool_lb_mode',
        'ttl_persistence', 'pools'
    ]

    @property
    def pools(self):
        result = []
        if self._values['pools'] is None:
            return []
        for pool in self._values['pools']:
            del pool['nameReference']
            for x in ['order', 'ratio']:
                if x in pool:
                    pool[x] = int(pool[x])
            result.append(pool)
        return result

    @property
    def failure_return_code_ttl(self):
        if self._values['failure_return_code_ttl'] is None:
            return None
        return int(self._values['failure_return_code_ttl'])

    @property
    def persist_cidr_ipv4(self):
        if self._values['persist_cidr_ipv4'] is None:
            return None
        return int(self._values['persist_cidr_ipv4'])

    @property
    def persist_cidr_ipv6(self):
        if self._values['persist_cidr_ipv6'] is None:
            return None
        return int(self._values['persist_cidr_ipv6'])

    @property
    def ttl_persistence(self):
        if self._values['ttl_persistence'] is None:
            return None
        return int(self._values['ttl_persistence'])


class ServerParameters(BaseParameters):
    api_map = {
        'fullPath': 'full_path',
        'exposeRouteDomains': 'expose_route_domains',
        'iqAllowPath': 'iq_allow_path',
        'iqAllowServiceCheck': 'iq_allow_service_check',
        'iqAllowSnmp': 'iq_allow_snmp',
        'limitCpuUsage': 'limit_cpu_usage',
        'limitCpuUsageStatus': 'limit_cpu_usage_status',
        'limitMaxBps': 'limit_max_bps',
        'limitMaxBpsStatus': 'limit_max_bps_status',
        'limitMaxConnections': 'limit_max_connections',
        'limitMaxConnectionsStatus': 'limit_max_connections_status',
        'limitMaxPps': 'limit_max_pps',
        'limitMaxPpsStatus': 'limit_max_pps_status',
        'limitMemAvail': 'limit_mem_available',
        'limitMemAvailStatus': 'limit_mem_available_status',
        'linkDiscovery': 'link_discovery',
        'proberFallback': 'prober_fallback',
        'proberPreference': 'prober_preference',
        'virtualServerDiscovery': 'virtual_server_discovery',
        'devicesReference': 'devices',
        'virtualServersReference': 'virtual_servers'
    }

    returnables = [
        'datacenter', 'enabled', 'disabled', 'expose_route_domains', 'iq_allow_path',
        'full_path', 'iq_allow_service_check', 'iq_allow_snmp', 'limit_cpu_usage',
        'limit_cpu_usage_status', 'limit_max_bps', 'limit_max_bps_status',
        'limit_max_connections', 'limit_max_connections_status', 'limit_max_pps',
        'limit_max_pps_status', 'limit_mem_available', 'limit_mem_available_status',
        'link_discovery', 'monitor', 'product', 'prober_fallback', 'prober_preference',
        'virtual_server_discovery', 'addresses', 'devices', 'virtual_servers'
    ]

    @property
    def product(self):
        if self._values['product'] is None:
            return None
        if self._values['product'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        return self._values['product']

    @property
    def devices(self):
        result = []
        if self._values['devices'] is None or 'items' not in self._values['devices']:
            return result
        for item in self._values['devices']['items']:
            self._remove_internal_keywords(item)
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            result.append(item)
        return result

    @property
    def virtual_servers(self):
        result = []
        if self._values['virtual_servers'] is None or 'items' not in self._values['virtual_servers']:
            return result
        for item in self._values['virtual_servers']['items']:
            self._remove_internal_keywords(item)
            if 'disabled' in item:
                if item['disabled'] in BOOLEANS_TRUE:
                    item['disabled'] = True
                else:
                    item['disabled'] = False
            if 'enabled' in item:
                if item['enabled'] in BOOLEANS_TRUE:
                    item['enabled'] = True
                else:
                    item['enabled'] = False
            if 'fullPath' in item:
                item['full_path'] = item.pop('fullPath')
            if 'limitMaxBps' in item:
                item['limit_max_bps'] = int(item.pop('limitMaxBps'))
            if 'limitMaxBpsStatus' in item:
                item['limit_max_bps_status'] = item.pop('limitMaxBpsStatus')
            if 'limitMaxConnections' in item:
                item['limit_max_connections'] = int(item.pop('limitMaxConnections'))
            if 'limitMaxConnectionsStatus' in item:
                item['limit_max_connections_status'] = item.pop('limitMaxConnectionsStatus')
            if 'limitMaxPps' in item:
                item['limit_max_pps'] = int(item.pop('limitMaxPps'))
            if 'limitMaxPpsStatus' in item:
                item['limit_max_pps_status'] = item.pop('limitMaxPpsStatus')
            if 'translationAddress' in item:
                item['translation_address'] = item.pop('translationAddress')
            if 'translationPort' in item:
                item['translation_port'] = int(item.pop('translationPort'))
            result.append(item)
        return result

    @property
    def limit_cpu_usage(self):
        if self._values['limit_cpu_usage'] is None:
            return None
        return int(self._values['limit_cpu_usage'])

    @property
    def limit_max_bps(self):
        if self._values['limit_max_bps'] is None:
            return None
        return int(self._values['limit_max_bps'])

    @property
    def limit_max_connections(self):
        if self._values['limit_max_connections'] is None:
            return None
        return int(self._values['limit_max_connections'])

    @property
    def limit_max_pps(self):
        if self._values['limit_max_pps'] is None:
            return None
        return int(self._values['limit_max_pps'])

    @property
    def limit_mem_available(self):
        if self._values['limit_mem_available'] is None:
            return None
        return int(self._values['limit_mem_available'])


class PoolFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        super(PoolFactManager, self).__init__(**kwargs)
        self.kwargs = kwargs

    def exec_module(self):
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        facts = manager.exec_module()
        result = dict(pool=facts)
        return result

    def get_manager(self, type):
        if type == 'typed':
            return TypedPoolFactManager(**self.kwargs)
        elif type == 'untyped':
            return UntypedPoolFactManager(**self.kwargs)


class TypedPoolFactManager(TypedManager):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        super(TypedPoolFactManager, self).__init__(**kwargs)
        self.want = PoolParameters(params=self.module.params)

    def read_facts(self, collection):
        results = []
        collection = self.read_collection_from_device(collection)
        for resource in collection:
            attrs = resource.attrs
            attrs['stats'] = self.read_stats_from_device(resource)
            params = PoolParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self, collection_name):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, collection_name)
        result = collection.get_collection(
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return result


class UntypedPoolFactManager(UntypedManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(UntypedPoolFactManager, self).__init__(**kwargs)
        self.want = PoolParameters(params=self.module.params)

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource.attrs
            attrs['stats'] = self.read_stats_from_device(resource)
            params = PoolParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        result = self.client.api.tm.gtm.pools.get_collection(
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return result


class WideIpFactManager(BaseManager):
    def exec_module(self):
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        facts = manager.exec_module()
        result = dict(wide_ip=facts)
        return result

    def get_manager(self, type):
        if type == 'typed':
            return TypedWideIpFactManager(**self.kwargs)
        elif type == 'untyped':
            return UntypedWideIpFactManager(**self.kwargs)


class TypedWideIpFactManager(TypedManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(TypedWideIpFactManager, self).__init__(**kwargs)
        self.want = WideIpParameters(params=self.module.params)

    def read_facts(self, collection):
        results = []
        collection = self.read_collection_from_device(collection)
        for resource in collection:
            attrs = resource.attrs
            params = WideIpParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self, collection_name):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, collection_name)
        result = collection.get_collection(
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return result


class UntypedWideIpFactManager(UntypedManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(UntypedWideIpFactManager, self).__init__(**kwargs)
        self.want = WideIpParameters(params=self.module.params)

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource.attrs
            params = WideIpParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        result = self.client.api.tm.gtm.wideips.get_collection(
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return result


class ServerFactManager(UntypedManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ServerFactManager, self).__init__(**kwargs)
        self.want = ServerParameters(params=self.module.params)

    def exec_module(self):
        facts = super(ServerFactManager, self).exec_module()
        result = dict(server=facts)
        return result

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            attrs = resource.attrs
            params = ServerParameters(params=attrs)
            results.append(params)
        return results

    def read_collection_from_device(self):
        result = self.client.api.tm.gtm.servers.get_collection(
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs
        self.want = Parameters(params=self.module.params)

    def exec_module(self):
        if not self.gtm_provisioned():
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )

        if 'all' in self.want.include:
            names = ['pool', 'wide_ip', 'server']
        else:
            names = self.want.include
        managers = [self.get_manager(name) for name in names]
        result = self.execute_managers(managers)
        if result:
            result['changed'] = True
        else:
            result['changed'] = False
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def execute_managers(self, managers):
        results = dict()
        for manager in managers:
            result = manager.exec_module()
            results.update(result)
        return results

    def get_manager(self, which):
        if 'pool' == which:
            return PoolFactManager(**self.kwargs)
        if 'wide_ip' == which:
            return WideIpFactManager(**self.kwargs)
        if 'server' == which:
            return ServerFactManager(**self.kwargs)

    def gtm_provisioned(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name='provisioned.cpu.gtm'
        )
        if int(resource.value) == 0:
            return False
        return True


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            include=dict(
                type='list',
                choices=[
                    'pool',
                    'wide_ip',
                    'server',
                ],
                required=True
            ),
            filter=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
