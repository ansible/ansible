#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigiq_device_info
short_description: Collect information from F5 BIG-IQ devices
description:
  - Collect information from F5 BIG-IQ devices.
  - This module was called C(bigiq_device_facts) before Ansible 2.9. The usage did not change.
version_added: 2.8
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the information returned to a given subset.
      - Can specify a list of values to include a larger subset.
      - Values can also be used with an initial C(!) to specify that a specific subset
        should not be collected.
    type: list
    required: True
    choices:
      - all
      - applications
      - managed-devices
      - purchased-pool-licenses
      - regkey-pools
      - system-info
      - vlans
      - "!all"
      - "!applications"
      - "!managed-devices"
      - "!purchased-pool-licenses"
      - "!regkey-pools"
      - "!system-info"
      - "!vlans"
extends_documentation_fragment: f5
notes:
  - With BIGIQ 7.0 and later, a few metadata fields not included/supported (for example, uptime, product_changelist, product_jobid)
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Collect BIG-IQ information
  bigiq_device_info:
    gather_subset:
      - system-info
      - vlans
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Collect all BIG-IQ information
  bigiq_device_info:
    gather_subset:
      - all
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Collect all BIG-IP information except trunks
  bigiq_device_info:
    gather_subset:
      - all
      - "!trunks"
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
applications:
  description: Application related information
  returned: When C(managed-devices) is specified in C(gather_subset).
  type: complex
  contains:
    protection_mode:
      description:
        - The type of F5 Web Application Security Service protection on the application.
      returned: changed
      type: str
      sample: Not Protected
    id:
      description:
        - ID of the application as known to the BIG-IQ.
      returned: changed
      type: str
      sample: 996baae8-5d1d-3662-8a2d-3612fa2aceae
    name:
      description:
        - Name of the application.
      returned: changed
      type: str
      sample: site12http.example.com
    status:
      description:
        - Current state of the application.
      returned: changed
      type: str
      sample: DEPLOYED
    transactions_per_second:
      description:
        - Current measurement of Transactions Per second being handled by the application.
      returned: changed
      type: float
      sample: 0.87
    connections:
      description:
        - Current number of connections established to the application.
      returned: changed
      type: float
      sample: 3.06
    new_connections:
      description:
        - Number of new connections being established per second.
      returned: changed
      type: float
      sample: 0.35
    response_time:
      description:
        - Measured response time of the application in milliseconds.
      returned: changed
      type: float
      sample: 0.02
    health:
      description:
        - Health of the application.
      returned: changed
      type: str
      sample: Good
    active_alerts:
      description:
        - Number of alerts active on the application.
      returned: changed
      type: int
      sample: 0
    bad_traffic:
      description:
        - Percent of traffic to application that is determined to be 'bad'.
        - This value is dependent on C(protection_mode) being enabled.
      returned: changed
      type: float
      sample: 1.7498
    enhanced_analytics:
      description:
        - Whether enhanced analytics is enabled for the application or not.
      returned: changed
      type: bool
      sample: yes
    bad_traffic_growth:
      description:
        - Whether or not Bad Traffic Growth alerts are configured to be triggered or not.
      returned: changed
      type: bool
      sample: no
  sample: hash/dictionary of values
managed_devices:
  description: Managed device related information.
  returned: When C(managed-devices) is specified in C(gather_subset).
  type: complex
  contains:
    address:
      description:
        - Address where the device was discovered.
      returned: changed
      type: str
      sample: 10.10.10.10
    build:
      description:
        - Build of the version.
      returned: changed
      type: str
      sample: 0.0.4
    device_uri:
      description:
        - URI to reach the management interface of the device.
      returned: changed
      type: str
      sample: "https://10.10.10.10:443"
    edition:
      description:
        - Edition string of the product version.
      returned: changed
      type: str
      sample: Final
    group_name:
      description:
        - BIG-IQ group that the device is a member of.
      returned: changed
      type: str
      sample: cm-bigip-allBigIpDevices
    hostname:
      description:
        - Discovered hostname of the device.
      returned: changed
      type: str
      sample: tier2labB1.lab.fp.foo.com
    https_port:
      description:
        - HTTPS port available on the management interface of the device.
      returned: changed
      type: int
      sample: 443
    is_clustered:
      description:
        - Whether the device is clustered or not.
      returned: changed
      type: bool
      sample: no
    is_license_expired:
      description:
        - Whether the license on the device is expired or not.
      returned: changed
      type: bool
      sample: yes
    is_virtual:
      description:
        - Whether the device is a virtual edition or not.
      returned: changed
      type: bool
      sample: yes
    machine_id:
      description:
        - Machine specific ID assigned to this device by BIG-IQ.
      returned: changed
      type: str
      sample: c141bc88-f734-4434-be64-a3e9ea98356e
    management_address:
      description:
        - IP address of the management interface on the device.
      returned: changed
      type: str
      sample: 10.10.10.10
    mcp_device_name:
      description:
        - Device name as known by MCPD on the BIG-IP.
      returned: changed
      type: str
      sample: /Common/tier2labB1.lab.fp.foo.com
    product:
      description:
        - Product that the managed device is identified as.
      returned: changed
      type: str
      sample: BIG-IP
    rest_framework_version:
      description:
        - REST framework version running on the device
      returned: changed
      type: str
      sample: 13.1.1-0.0.4
    self_link:
      description:
        - Internal reference to the managed device in BIG-IQ.
      returned: changed
      type: str
      sample: "https://localhost/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices/c141bc88-f734-4434-be64-a3e9ea98356e"
    slots:
      description:
        - Volumes on the device and versions of software installed in those volumes.
      returned: changed
      type: complex
      sample: {"volume": "HD1.1", "product": "BIG-IP", "version": "13.1.1", "build": "0.0.4", "isActive": "yes"}
    state:
      description:
        - State of the device.
      returned: changed
      type: str
      sample: ACTIVE
    tags:
      description:
        - Misc tags that are assigned to the device.
      returned: changed
      type: complex
      sample: {'BIGIQ_tier_2_device': '2018-08-22T13:30:47.693-07:00', 'BIGIQ_SSG_name': 'tim-ssg'}
    trust_domain_guid:
      description:
        - GUID of the trust domain the device is part of.
      returned: changed
      type: str
      sample: 40ddf541-e604-4905-bde3005056813e36
    uuid:
      description:
        - UUID of the device in BIG-IQ.
      returned: changed
      type: str
      sample: c141bc88-f734-4434-be64-a3e9ea98356e
    version:
      description:
        - Version of TMOS installed on the device.
      returned: changed
      type: str
      sample: 13.1.1
  sample: hash/dictionary of values
purchased_pool_licenses:
  description: Purchased Pool License related information.
  returned: When C(purchased-pool-licenses) is specified in C(gather_subset).
  type: complex
  contains:
    base_reg_key:
      description:
        - Base registration key of the purchased pool
      returned: changed
      type: str
      sample: XXXXX-XXXXX-XXXXX-XXXXX-XXXXXXX
    dossier:
      description:
        - Dossier of the purchased pool license
      returned: changed
      type: str
      sample: d6bd4b8ba5...e9a1a1199b73af9932948a
    free_device_licenses:
      description:
        - Number of free licenses remaining.
      returned: changed
      type: int
      sample: 34
    name:
      description:
        - Name of the purchased pool
      returned: changed
      type: str
      sample: my-pool1
    state:
      description:
        - State of the purchased pool license
      returned: changed
      type: str
      sample: LICENSED
    total_device_licenses:
      description:
        - Total number of licenses in the pool.
      returned: changed
      type: int
      sample: 40
    uuid:
      description:
        - UUID of the purchased pool license
      returned: changed
      type: str
      sample: b2112329-cba7-4f1f-9a26-fab9be416d60
    vendor:
      description:
        - Vendor who provided the license
      returned: changed
      type: str
      sample: F5 Networks, Inc
    licensed_date_time:
      description:
        - Timestamp that the pool was licensed.
      returned: changed
      type: str
      sample: "2018-09-10T00:00:00-07:00"
    licensed_version:
      description:
        - Version of BIG-IQ that is licensed.
      returned: changed
      type: str
      sample: 6.0.1
    evaluation_start_date_time:
      description:
        - Date that evaluation license starts.
      returned: changed
      type: str
      sample: "2018-09-09T00:00:00-07:00"
    evaluation_end_date_time:
      description:
        - Date that evaluation license ends.
      returned: changed
      type: str
      sample: "2018-10-11T00:00:00-07:00"
    license_end_date_time:
      description:
        - Date that the license expires.
      returned: changed
      type: str
      sample: "2018-10-11T00:00:00-07:00"
    license_start_date_time:
      description:
        - Date that the license starts.
      returned: changed
      type: str
      sample: "2018-09-09T00:00:00-07:00"
    registration_key:
      description:
        - Purchased pool license key.
      returned: changed
      type: str
      sample: XXXXX-XXXXX-XXXXX-XXXXX-XXXXXXX
  sample: hash/dictionary of values
regkey_pools:
  description: Regkey Pool related information.
  returned: When C(regkey-pools) is specified in C(gather_subset).
  type: complex
  contains:
    name:
      description:
        - Name of the regkey pool.
      returned: changed
      type: str
      sample: pool1
    id:
      description:
        - ID of the regkey pool.
      returned: changed
      type: str
      sample: 4f9b565c-0831-4657-b6c2-6dde6182a502
    total_offerings:
      description:
        - Total number of offerings in the pool
      returned: changed
      type: int
      sample: 10
    offerings:
      description: List of the offerings in the pool.
      type: complex
      contains:
        dossier:
          description:
            - Dossier of the license.
          returned: changed
          type: str
          sample: d6bd4b8ba5...e9a1a1199b73af9932948a
        name:
          description:
            - Name of the regkey.
          returned: changed
          type: str
          sample: regkey1
        state:
          description:
            - State of the regkey license
          returned: changed
          type: str
          sample: LICENSED
        licensed_date_time:
          description:
            - Timestamp that the regkey was licensed.
          returned: changed
          type: str
          sample: "2018-09-10T00:00:00-07:00"
        licensed_version:
          description:
            - Version of BIG-IQ that is licensed.
          returned: changed
          type: str
          sample: 6.0.1
        evaluation_start_date_time:
          description:
            - Date that evaluation license starts.
          returned: changed
          type: str
          sample: "2018-09-09T00:00:00-07:00"
        evaluation_end_date_time:
          description:
            - Date that evaluation license ends.
          returned: changed
          type: str
          sample: "2018-10-11T00:00:00-07:00"
        license_end_date_time:
          description:
            - Date that the license expires.
          returned: changed
          type: str
          sample: "2018-10-11T00:00:00-07:00"
        license_start_date_time:
          description:
            - Date that the license starts.
          returned: changed
          type: str
          sample: "2018-09-09T00:00:00-07:00"
        registration_key:
          description:
            - Registration license key.
          returned: changed
          type: str
          sample: XXXXX-XXXXX-XXXXX-XXXXX-XXXXXXX
      sample: hash/dictionary of values
  sample: hash/dictionary of values
system_info:
  description: System info related information.
  returned: When C(system-info) is specified in C(gather_subset).
  type: complex
  contains:
    base_mac_address:
      description:
        - Media Access Control address (MAC address) of the device.
      returned: changed
      type: str
      sample: "fa:16:3e:c3:42:6f"
    marketing_name:
      description:
        - Marketing name of the device platform.
      returned: changed
      type: str
      sample: BIG-IQ Virtual Edition
    time:
      description:
        - Mapping of the current time information to specific time-named keys.
      returned: changed
      type: complex
      contains:
        day:
          description:
            - The current day of the month, in numeric form.
          returned: changed
          type: int
          sample: 7
        hour:
          description:
            - The current hour of the day in 24-hour form.
          returned: changed
          type: int
          sample: 18
        minute:
          description:
            - The current minute of the hour.
          returned: changed
          type: int
          sample: 16
        month:
          description:
            - The current month, in numeric form.
          returned: changed
          type: int
          sample: 6
        second:
          description:
            - The current second of the minute.
          returned: changed
          type: int
          sample: 51
        year:
          description:
            - The current year in 4-digit form.
          returned: changed
          type: int
          sample: 2018
    hardware_information:
      description:
        - Information related to the hardware (drives and CPUs) of the system.
      type: complex
      returned: changed
      contains:
        model:
          description:
            - The model of the hardware.
          type: str
          sample: Virtual Disk
        name:
          description:
            - The name of the hardware.
          type: str
          sample: HD1
        type:
          description:
            - The type of hardware.
          type: str
          sample: physical-disk
        versions:
          description:
            - Hardware specific properties
          type: complex
          contains:
            name:
              description:
                - Name of the property
              type: str
              sample: Size
            version:
              description:
                - Value of the property
              type: str
              sample: 154.00G
    is_admin_password_changed:
      description:
        - Whether the admin password was changed from its default or not.
      returned: changed
      type: bool
      sample: yes
    is_root_password_changed:
      description:
        - Whether the root password was changed from its default or not.
      returned: changed
      type: bool
      sample: no
    is_system_setup:
      description:
        - Whether the system has been setup or not.
      returned: changed
      type: bool
      sample: yes
    package_edition:
      description:
        - Displays the software edition.
      returned: changed
      type: str
      sample: Point Release 7
    package_version:
      description:
        - A string combining the C(product_build) and C(product_build_date).
      type: str
      sample: "Build 0.0.1 - Tue May 15 15:26:30 PDT 2018"
    product_code:
      description:
        - Code identifying the product.
      type: str
      sample: BIG-IQ
    product_build:
      description:
        - Build version of the release version.
      type: str
      sample: 0.0.1
    product_version:
      description:
        - Major product version of the running software.
      type: str
      sample: 6.0.0
    product_built:
      description:
        - Unix timestamp of when the product was built.
      type: int
      sample: 180515152630
    product_build_date:
      description:
        - Human readable build date.
      type: str
      sample: "Tue May 15 15:26:30 PDT 2018"
    product_changelist:
      description:
        - Changelist that product branches from.
        - Not supported with BIGIQ 7.0 and later versions.
      type: int
      sample: 2557198
    product_jobid:
      description:
        - ID of the job that built the product version.
        - Not supported with BIGIQ 7.0 and later versions.
      type: int
      sample: 1012030
    chassis_serial:
      description:
        - Serial of the chassis
      type: str
      sample: 11111111-2222-3333-444444444444
    host_board_part_revision:
      description:
        - Revision of the host board.
      type: str
    host_board_serial:
      description:
        - Serial of the host board.
      type: str
    platform:
      description:
        - Platform identifier.
      type: str
      sample: Z100
    switch_board_part_revision:
      description:
        - Switch board revision.
      type: str
    switch_board_serial:
      description:
        - Serial of the switch board.
      type: str
    uptime:
      description:
        - Time, in seconds, since the system booted.
        - Not supported with BIGIQ 7.0 and later versions.
      type: int
      sample: 603202
  sample: hash/dictionary of values
vlans:
  description: List of VLAN information.
  returned: When C(vlans) is specified in C(gather_subset).
  type: complex
  contains:
    auto_lasthop:
      description:
        - Allows the system to send return traffic to the MAC address that transmitted the
          request, even if the routing table points to a different network or interface.
      returned: changed
      type: str
      sample: enabled
    cmp_hash_algorithm:
      description:
        - Specifies how the traffic on the VLAN will be disaggregated.
      returned: changed
      type: str
      sample: default
    description:
      description:
        - Description of the VLAN.
      returned: changed
      type: str
      sample: My vlan
    failsafe_action:
      description:
        - Action for the system to take when the fail-safe mechanism is triggered.
      returned: changed
      type: str
      sample: reboot
    failsafe_enabled:
      description:
        - Whether failsafe is enabled or not.
      returned: changed
      type: bool
      sample: yes
    failsafe_timeout:
      description:
        - Number of seconds that an active unit can run without detecting network traffic
          on this VLAN before it starts a failover.
      returned: changed
      type: int
      sample: 90
    if_index:
      description:
        - Index assigned to this VLAN. It is a unique identifier assigned for all objects
          displayed in the SNMP IF-MIB.
      returned: changed
      type: int
      sample: 176
    learning_mode:
      description:
        - Whether switch ports placed in the VLAN are configured for switch learning,
          forwarding only, or dropped.
      returned: changed
      type: str
      sample: enable-forward
    interfaces:
      description:
        - List of tagged or untagged interfaces and trunks that you want to configure for the VLAN.
      returned: changed
      type: complex
      contains:
        full_path:
          description:
            - Full name of the resource as known to BIG-IP.
          returned: changed
          type: str
          sample: 1.3
        name:
          description:
            - Relative name of the resource in BIG-IP.
          returned: changed
          type: str
          sample: 1.3
        tagged:
          description:
            - Whether the interface is tagged or not.
          returned: changed
          type: bool
          sample: no
    mtu:
      description:
        - Specific maximum transition unit (MTU) for the VLAN.
      returned: changed
      type: int
      sample: 1500
    sflow_poll_interval:
      description:
        - Maximum interval in seconds between two pollings.
      returned: changed
      type: int
      sample: 0
    sflow_poll_interval_global:
      description:
        - Whether the global VLAN poll-interval setting, overrides the object-level
          poll-interval setting.
      returned: changed
      type: bool
      sample: no
    sflow_sampling_rate:
      description:
        - Ratio of packets observed to the samples generated.
      returned: changed
      type: int
      sample: 0
    sflow_sampling_rate_global:
      description:
        - Whether the global VLAN sampling-rate setting, overrides the object-level
          sampling-rate setting.
      returned: changed
      type: bool
      sample: yes
    source_check_enabled:
      description:
        - Specifies that only connections that have a return route in the routing table are accepted.
      returned: changed
      type: bool
      sample: yes
    true_mac_address:
      description:
        - Media access control (MAC) address for the lowest-numbered interface assigned to this VLAN.
      returned: changed
      type: str
      sample: "fa:16:3e:10:da:ff"
    tag:
      description:
        - Tag number for the VLAN.
      returned: changed
      type: int
      sample: 30
  sample: hash/dictionary of values
'''

import copy
import datetime
import math
import re

from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigiq import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import bigiq_version
except ImportError:
    from ansible.module_utils.network.f5.bigiq import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import bigiq_version


def parseStats(entry):
    if 'description' in entry:
        return entry['description']
    elif 'value' in entry:
        return entry['value']
    elif 'entries' in entry or 'nestedStats' in entry and 'entries' in entry['nestedStats']:
        if 'entries' in entry:
            entries = entry['entries']
        else:
            entries = entry['nestedStats']['entries']
        result = None

        for name in entries:
            entry = entries[name]
            if 'https://localhost' in name:
                name = name.split('/')
                name = name[-1]
                if result and isinstance(result, list):
                    result.append(parseStats(entry))
                elif result and isinstance(result, dict):
                    result[name] = parseStats(entry)
                else:
                    try:
                        int(name)
                        result = list()
                        result.append(parseStats(entry))
                    except ValueError:
                        result = dict()
                        result[name] = parseStats(entry)
            else:
                if '.' in name:
                    names = name.split('.')
                    key = names[0]
                    value = names[1]
                    if not result[key]:
                        result[key] = {}
                    result[key][value] = parseStats(entry)
                else:
                    if result and isinstance(result, list):
                        result.append(parseStats(entry))
                    elif result and isinstance(result, dict):
                        result[name] = parseStats(entry)
                    else:
                        try:
                            int(name)
                            result = list()
                            result.append(parseStats(entry))
                        except ValueError:
                            result = dict()
                            result[name] = parseStats(entry)
        return result


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        return results


class Parameters(AnsibleF5Parameters):
    @property
    def gather_subset(self):
        if isinstance(self._values['gather_subset'], string_types):
            self._values['gather_subset'] = [self._values['gather_subset']]
        elif not isinstance(self._values['gather_subset'], list):
            raise F5ModuleError(
                "The specified gather_subset must be a list."
            )
        tmp = list(set(self._values['gather_subset']))
        tmp.sort()
        self._values['gather_subset'] = tmp

        return self._values['gather_subset']


class BaseParameters(Parameters):
    @property
    def enabled(self):
        return flatten_boolean(self._values['enabled'])

    @property
    def disabled(self):
        return flatten_boolean(self._values['disabled'])

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


class ApplicationsParameters(BaseParameters):
    api_map = {
        'protectionMode': 'protection_mode',
        'transactionsPerSecond': 'transactions_per_second',
        'newConnections': 'new_connections',
        'responseTime': 'response_time',
        'activeAlerts': 'active_alerts',
        'badTraffic': 'bad_traffic',
        'enhancedAnalytics': 'enhanced_analytics',
        'badTrafficGrowth': 'bad_traffic_growth'
    }

    returnables = [
        'protection_mode',
        'id',
        'name',
        'status',
        'transactions_per_second',
        'connections',
        'new_connections',
        'response_time',
        'health',
        'active_alerts',
        'bad_traffic',
        'enhanced_analytics',
        'bad_traffic_growth',
    ]

    @property
    def enhanced_analytics(self):
        return flatten_boolean(self._values['enhanced_analytics'])

    @property
    def bad_traffic_growth(self):
        return flatten_boolean(self._values['bad_traffic_growth'])


class ApplicationsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ApplicationsFactManager, self).__init__(**kwargs)
        self.want = ApplicationsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(applications=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['name'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ApplicationsParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/ap/query/v1/tenants/default/reports/AllApplicationsList".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            return response['result']['items']
        except KeyError:
            return []


class ManagedDevicesParameters(BaseParameters):
    api_map = {
        'deviceUri': 'device_uri',
        'groupName': 'group_name',
        'httpsPort': 'https_port',
        'isClustered': 'is_clustered',
        'isLicenseExpired': 'is_license_expired',
        'isVirtual': 'is_virtual',
        'machineId': 'machine_id',
        'managementAddress': 'management_address',
        'mcpDeviceName': 'mcp_device_name',
        'restFrameworkVersion': 'rest_framework_version',
        'selfLink': 'self_link',
        'trustDomainGuid': 'trust_domain_guid',
    }

    returnables = [
        'address',
        'build',
        'device_uri',
        'edition',
        'group_name',
        'hostname',
        'https_port',
        'is_clustered',
        'is_license_expired',
        'is_virtual',
        'machine_id',
        'management_address',
        'mcp_device_name',
        'product',
        'rest_framework_version',
        'self_link',
        'slots',
        'state',
        'tags',
        'trust_domain_guid',
        'uuid',
        'version',
    ]

    @property
    def slots(self):
        result = []
        if self._values['slots'] is None:
            return None
        for x in self._values['slots']:
            x['is_active'] = flatten_boolean(x.pop('isActive', False))
            result.append(x)
        return result

    @property
    def tags(self):
        if self._values['tags'] is None:
            return None
        result = dict((x['name'], x['value']) for x in self._values['tags'])
        return result

    @property
    def https_port(self):
        return int(self._values['https_port'])

    @property
    def is_clustered(self):
        return flatten_boolean(self._values['is_clustered'])

    @property
    def is_license_expired(self):
        return flatten_boolean(self._values['is_license_expired'])

    @property
    def is_virtual(self):
        return flatten_boolean(self._values['is_virtual'])


class ManagedDevicesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(ManagedDevicesFactManager, self).__init__(**kwargs)
        self.want = ManagedDevicesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(managed_devices=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['hostname'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = ManagedDevicesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class PurchasedPoolLicensesParameters(BaseParameters):
    api_map = {
        'baseRegKey': 'base_reg_key',
        'freeDeviceLicenses': 'free_device_licenses',
        'licenseState': 'license_state',
        'totalDeviceLicenses': 'total_device_licenses',
    }

    returnables = [
        'base_reg_key',
        'dossier',
        'free_device_licenses',
        'name',
        'state',
        'total_device_licenses',
        'uuid',

        # license_state facts
        'vendor',
        'licensed_date_time',
        'licensed_version',
        'evaluation_start_date_time',
        'evaluation_end_date_time',
        'license_end_date_time',
        'license_start_date_time',
        'registration_key',
    ]

    @property
    def registration_key(self):
        try:
            return self._values['license_state']['registrationKey']
        except KeyError:
            return None

    @property
    def license_start_date_time(self):
        try:
            return self._values['license_state']['licenseStartDateTime']
        except KeyError:
            return None

    @property
    def license_end_date_time(self):
        try:
            return self._values['license_state']['licenseEndDateTime']
        except KeyError:
            return None

    @property
    def evaluation_end_date_time(self):
        try:
            return self._values['license_state']['evaluationEndDateTime']
        except KeyError:
            return None

    @property
    def evaluation_start_date_time(self):
        try:
            return self._values['license_state']['evaluationStartDateTime']
        except KeyError:
            return None

    @property
    def licensed_version(self):
        try:
            return self._values['license_state']['licensedVersion']
        except KeyError:
            return None

    @property
    def licensed_date_time(self):
        try:
            return self._values['license_state']['licensedDateTime']
        except KeyError:
            return None

    @property
    def vendor(self):
        try:
            return self._values['license_state']['vendor']
        except KeyError:
            return None


class PurchasedPoolLicensesFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(PurchasedPoolLicensesFactManager, self).__init__(**kwargs)
        self.want = PurchasedPoolLicensesParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(purchased_pool_licenses=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['name'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = PurchasedPoolLicensesParameters(params=resource)
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/purchased-pool/licenses".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            return response['items']
        except KeyError:
            return []


class RegkeyPoolsParameters(BaseParameters):
    api_map = {

    }

    returnables = [
        'name',
        'id',
        'offerings',
        'total_offerings',
    ]


class RegkeyPoolsOfferingParameters(BaseParameters):
    api_map = {
        'regKey': 'registration_key',
        'licenseState': 'license_state',
        'status': 'state',
    }

    returnables = [
        'name',
        'dossier',
        'state',

        # license_state facts
        'licensed_date_time',
        'licensed_version',
        'evaluation_start_date_time',
        'evaluation_end_date_time',
        'license_end_date_time',
        'license_start_date_time',
        'registration_key',
    ]

    @property
    def registration_key(self):
        try:
            return self._values['license_state']['registrationKey']
        except KeyError:
            return None

    @property
    def license_start_date_time(self):
        try:
            return self._values['license_state']['licenseStartDateTime']
        except KeyError:
            return None

    @property
    def license_end_date_time(self):
        try:
            return self._values['license_state']['licenseEndDateTime']
        except KeyError:
            return None

    @property
    def evaluation_end_date_time(self):
        try:
            return self._values['license_state']['evaluationEndDateTime']
        except KeyError:
            return None

    @property
    def evaluation_start_date_time(self):
        try:
            return self._values['license_state']['evaluationStartDateTime']
        except KeyError:
            return None

    @property
    def licensed_version(self):
        try:
            return self._values['license_state']['licensedVersion']
        except KeyError:
            return None

    @property
    def licensed_date_time(self):
        try:
            return self._values['license_state']['licensedDateTime']
        except KeyError:
            return None

    @property
    def vendor(self):
        try:
            return self._values['license_state']['vendor']
        except KeyError:
            return None


class RegkeyPoolsFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(RegkeyPoolsFactManager, self).__init__(**kwargs)
        self.want = RegkeyPoolsParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(regkey_pools=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['name'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            params = RegkeyPoolsParameters(params=resource)
            offerings = self.read_offerings_from_device(resource['id'])
            params.update({'total_offerings': len(offerings)})
            for offering in offerings:
                params2 = RegkeyPoolsOfferingParameters(params=offering)
                params.update({'offerings': params2.to_return()})
            results.append(params)
        return results

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            return response['items']
        except KeyError:
            return []

    def read_offerings_from_device(self, license):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            license,
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            return response['items']
        except KeyError:
            return []


class SystemInfoParameters(BaseParameters):
    api_map = {
        'isSystemSetup': 'is_system_setup',
        'isAdminPasswordChanged': 'is_admin_password_changed',
        'isRootPasswordChanged': 'is_root_password_changed'
    }

    returnables = [
        'base_mac_address',
        'chassis_serial',
        'hardware_information',
        'host_board_part_revision',
        'host_board_serial',
        'is_admin_password_changed',
        'is_root_password_changed',
        'is_system_setup',
        'marketing_name',
        'package_edition',
        'package_version',
        'platform',
        'product_build',
        'product_build_date',
        'product_built',
        'product_changelist',
        'product_code',
        'product_information',
        'product_jobid',
        'product_version',
        'switch_board_part_revision',
        'switch_board_serial',
        'time',
        'uptime',
    ]

    @property
    def is_admin_password_changed(self):
        return flatten_boolean(self._values['is_admin_password_changed'])

    @property
    def is_root_password_changed(self):
        return flatten_boolean(self._values['is_root_password_changed'])

    @property
    def is_system_setup(self):
        if self._values['is_system_setup'] is None:
            return 'no'
        return flatten_boolean(self._values['is_system_setup'])

    @property
    def chassis_serial(self):
        if self._values['system-info'] is None:
            return None

        # Yes, this is still called "bigip" even though this is querying the BIG-IQ
        # product. This is likely due to BIG-IQ inheriting TMOS.
        if 'bigipChassisSerialNum' not in self._values['system-info'][0]:
            return None
        return self._values['system-info'][0]['bigipChassisSerialNum']

    @property
    def switch_board_serial(self):
        if self._values['system-info'] is None:
            return None
        if 'switchBoardSerialNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['switchBoardSerialNum'].strip() == '':
            return None
        return self._values['system-info'][0]['switchBoardSerialNum']

    @property
    def switch_board_part_revision(self):
        if self._values['system-info'] is None:
            return None
        if 'switchBoardPartRevNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['switchBoardPartRevNum'].strip() == '':
            return None
        return self._values['system-info'][0]['switchBoardPartRevNum']

    @property
    def platform(self):
        if self._values['system-info'] is None:
            return None
        return self._values['system-info'][0]['platform']

    @property
    def host_board_serial(self):
        if self._values['system-info'] is None:
            return None
        if 'hostBoardSerialNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['hostBoardSerialNum'].strip() == '':
            return None
        return self._values['system-info'][0]['hostBoardSerialNum']

    @property
    def host_board_part_revision(self):
        if self._values['system-info'] is None:
            return None
        if 'hostBoardPartRevNum' not in self._values['system-info'][0]:
            return None
        if self._values['system-info'][0]['hostBoardPartRevNum'].strip() == '':
            return None
        return self._values['system-info'][0]['hostBoardPartRevNum']

    @property
    def package_edition(self):
        return self._values['Edition']

    @property
    def package_version(self):
        return 'Build {0} - {1}'.format(self._values['Build'], self._values['Date'])

    @property
    def product_build(self):
        return self._values['Build']

    @property
    def product_build_date(self):
        return self._values['Date']

    @property
    def product_built(self):
        if 'version_info' not in self._values:
            return None
        if 'Built' in self._values['version_info']:
            return int(self._values['version_info']['Built'])

    @property
    def product_changelist(self):
        if 'version_info' not in self._values:
            return None
        if 'Changelist' in self._values['version_info']:
            return int(self._values['version_info']['Changelist'])

    @property
    def product_jobid(self):
        if 'version_info' not in self._values:
            return None
        if 'JobID' in self._values['version_info']:
            return int(self._values['version_info']['JobID'])

    @property
    def product_code(self):
        return self._values['Product']

    @property
    def product_version(self):
        return self._values['Version']

    @property
    def hardware_information(self):
        if self._values['hardware-version'] is None:
            return None
        self._transform_name_attribute(self._values['hardware-version'])
        result = [v for k, v in iteritems(self._values['hardware-version'])]
        return result

    def _transform_name_attribute(self, entry):
        if isinstance(entry, dict):
            tmp = copy.deepcopy(entry)
            for k, v in iteritems(tmp):
                if k == 'tmName':
                    entry['name'] = entry.pop('tmName')
                self._transform_name_attribute(v)
        elif isinstance(entry, list):
            for k in entry:
                self._transform_name_attribute(k)
        else:
            return

    @property
    def time(self):
        if self._values['fullDate'] is None:
            return None
        date = datetime.datetime.strptime(self._values['fullDate'], "%Y-%m-%dT%H:%M:%SZ")
        result = dict(
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            month=date.month,
            second=date.second,
            year=date.year
        )
        return result

    @property
    def marketing_name(self):
        if self._values['platform'] is None:
            return None
        return self._values['platform'][0]['marketingName']

    @property
    def base_mac_address(self):
        if self._values['platform'] is None:
            return None
        return self._values['platform'][0]['baseMac']


class SystemInfoFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(SystemInfoFactManager, self).__init__(**kwargs)
        self.want = SystemInfoParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(system_info=facts)
        return result

    def _exec_module(self):
        facts = self.read_facts()
        results = facts.to_return()
        return results

    def read_facts(self):
        collection = self.read_collection_from_device()
        params = SystemInfoParameters(params=collection)
        return params

    def read_collection_from_device(self):
        result = dict()
        tmp = self.read_hardware_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_system_setup_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_clock_info_from_device()
        if tmp:
            result.update(tmp)

        tmp = self.read_version_info_from_device()
        if tmp:
            result.update(tmp)

        if LooseVersion(bigiq_version(self.client)) < LooseVersion('7.0.0'):
            tmp = self.read_uptime_info_from_device()
            if tmp:
                result.update(tmp)

            tmp = self.read_version_file_info_from_device()
            if tmp:
                result.update(tmp)

        return result

    def read_system_setup_from_device(self):
        uri = "https://{0}:{1}/mgmt/shared/system/setup".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return response

    def read_version_file_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "cat /VERSION"'
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            pattern = r'^(?P<key>(Product|Build|Sequence|BaseBuild|Edition|Date|Built|Changelist|JobID))\:(?P<value>.*)'
            result = response['commandResult'].strip()
        except KeyError:
            return None

        if 'No such file or directory' in result:
            return None

        lines = response['commandResult'].split("\n")
        result = dict()
        for line in lines:
            if not line:
                continue
            matches = re.match(pattern, line)
            if matches:
                result[matches.group('key')] = matches.group('value').strip()

        if result:
            return dict(
                version_info=result
            )

    def read_uptime_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "cat /proc/uptime"'
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        try:
            parts = response['commandResult'].strip().split(' ')
            return dict(
                uptime=math.floor(float(parts[0]))
            )
        except KeyError:
            pass

    def read_hardware_info_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/hardware".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        return result

    def read_clock_info_from_device(self):
        """Parses clock info from the REST API

        The clock stat returned from the REST API (at the time of 13.1.0.7)
        is similar to the following.

        {
            "kind": "tm:sys:clock:clockstats",
            "selfLink": "https://localhost/mgmt/tm/sys/clock?ver=13.1.0.4",
            "entries": {
                "https://localhost/mgmt/tm/sys/clock/0": {
                    "nestedStats": {
                        "entries": {
                            "fullDate": {
                                "description": "2018-06-05T13:38:33Z"
                            }
                        }
                    }
                }
            }
        }

        Parsing this data using the ``parseStats`` method, yields a list of
        the clock stats in a format resembling that below.

        [{'fullDate': '2018-06-05T13:41:05Z'}]

        Therefore, this method cherry-picks the first entry from this list
        and returns it. There can be no other items in this list.

        Returns:
            A dict mapping keys to the corresponding clock stats. For
            example:

            {'fullDate': '2018-06-05T13:41:05Z'}

            There should never not be a clock stat, unless by chance it
            is removed from the API in the future, or changed to a different
            API endpoint.

        Raises:
            F5ModuleError: A non-successful HTTP code was returned or a JSON
                           response was not found.
        """
        uri = "https://{0}:{1}/mgmt/tm/sys/clock".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        if result is None:
            return None
        return result[0]

    def read_version_info_from_device(self):
        """Parses version info from the REST API

        The version stat returned from the REST API (at the time of 13.1.0.7)
        is similar to the following.

        {
            "kind": "tm:sys:version:versionstats",
            "selfLink": "https://localhost/mgmt/tm/sys/version?ver=13.1.0.4",
            "entries": {
                "https://localhost/mgmt/tm/sys/version/0": {
                    "nestedStats": {
                        "entries": {
                            "Build": {
                                "description": "0.0.6"
                            },
                            "Date": {
                                "description": "Tue Mar 13 20:10:42 PDT 2018"
                            },
                            "Edition": {
                                "description": "Point Release 4"
                            },
                            "Product": {
                                "description": "BIG-IP"
                            },
                            "Title": {
                                "description": "Main Package"
                            },
                            "Version": {
                                "description": "13.1.0.4"
                            }
                        }
                    }
                }
            }
        }

        Parsing this data using the ``parseStats`` method, yields a list of
        the clock stats in a format resembling that below.

        [{'Build': '0.0.6', 'Date': 'Tue Mar 13 20:10:42 PDT 2018',
          'Edition': 'Point Release 4', 'Product': 'BIG-IP', 'Title': 'Main Package',
          'Version': '13.1.0.4'}]

        Therefore, this method cherry-picks the first entry from this list
        and returns it. There can be no other items in this list.

        Returns:
            A dict mapping keys to the corresponding clock stats. For
            example:

            {'Build': '0.0.6', 'Date': 'Tue Mar 13 20:10:42 PDT 2018',
             'Edition': 'Point Release 4', 'Product': 'BIG-IP', 'Title': 'Main Package',
             'Version': '13.1.0.4'}

            There should never not be a version stat, unless by chance it
            is removed from the API in the future, or changed to a different
            API endpoint.

        Raises:
            F5ModuleError: A non-successful HTTP code was returned or a JSON
                           response was not found.
        """
        uri = "https://{0}:{1}/mgmt/tm/sys/version".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        if result is None:
            return None
        return result[0]


class VlansParameters(BaseParameters):
    api_map = {
        'autoLasthop': 'auto_lasthop',
        'cmpHash': 'cmp_hash_algorithm',
        'failsafeAction': 'failsafe_action',
        'failsafe': 'failsafe_enabled',
        'failsafeTimeout': 'failsafe_timeout',
        'ifIndex': 'if_index',
        'learning': 'learning_mode',
        'interfacesReference': 'interfaces',
        'sourceChecking': 'source_check_enabled',
        'fullPath': 'full_path'
    }

    returnables = [
        'full_path',
        'name',
        'auto_lasthop',
        'cmp_hash_algorithm',
        'description',
        'failsafe_action',
        'failsafe_enabled',
        'failsafe_timeout',
        'if_index',
        'learning_mode',
        'interfaces',
        'mtu',
        'sflow_poll_interval',
        'sflow_poll_interval_global',
        'sflow_sampling_rate',
        'sflow_sampling_rate_global',
        'source_check_enabled',
        'true_mac_address',
        'tag',
    ]

    @property
    def interfaces(self):
        if self._values['interfaces'] is None:
            return None
        if 'items' not in self._values['interfaces']:
            return None
        result = []
        for item in self._values['interfaces']['items']:
            tmp = dict(
                name=item['name'],
                full_path=item['fullPath']
            )
            if 'tagged' in item:
                tmp['tagged'] = 'yes'
            else:
                tmp['tagged'] = 'no'
            result.append(tmp)
        return result

    @property
    def sflow_poll_interval(self):
        return int(self._values['sflow']['pollInterval'])

    @property
    def sflow_poll_interval_global(self):
        return flatten_boolean(self._values['sflow']['pollIntervalGlobal'])

    @property
    def sflow_sampling_rate(self):
        return int(self._values['sflow']['samplingRate'])

    @property
    def sflow_sampling_rate_global(self):
        return flatten_boolean(self._values['sflow']['samplingRateGlobal'])

    @property
    def source_check_state(self):
        return flatten_boolean(self._values['source_check_state'])

    @property
    def true_mac_address(self):
        if self._values['stats']['macTrue'] in [None, 'none']:
            return None
        return self._values['stats']['macTrue']

    @property
    def tag(self):
        return self._values['stats']['id']

    @property
    def failsafe_enabled(self):
        return flatten_boolean(self._values['failsafe_enabled'])


class VlansFactManager(BaseManager):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        super(VlansFactManager, self).__init__(**kwargs)
        self.want = VlansParameters(params=self.module.params)

    def exec_module(self):
        facts = self._exec_module()
        result = dict(vlans=facts)
        return result

    def _exec_module(self):
        results = []
        facts = self.read_facts()
        for item in facts:
            attrs = item.to_return()
            results.append(attrs)
        results = sorted(results, key=lambda k: k['full_path'])
        return results

    def read_facts(self):
        results = []
        collection = self.read_collection_from_device()
        for resource in collection:
            resource.update(self.read_stats(resource['fullPath']))
            params = VlansParameters(params=resource)
            results.append(params)
        return results

    def read_stats(self, resource):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=resource)

        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        result = parseStats(response)
        return result

    def read_collection_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/?expandSubcollections=true".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'items' not in response:
            return []
        result = response['items']
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs
        self.want = Parameters(params=self.module.params)
        self.managers = {
            'applications': dict(
                manager=ApplicationsFactManager,
                client=F5RestClient,
            ),
            'managed-devices': dict(
                manager=ManagedDevicesFactManager,
                client=F5RestClient,
            ),
            'purchased-pool-licenses': dict(
                manager=PurchasedPoolLicensesFactManager,
                client=F5RestClient,
            ),
            'regkey-pools': dict(
                manager=RegkeyPoolsFactManager,
                client=F5RestClient,
            ),
            'system-info': dict(
                manager=SystemInfoFactManager,
                client=F5RestClient,
            ),
            'vlans': dict(
                manager=VlansFactManager,
                client=F5RestClient,
            ),
        }

    def exec_module(self):
        self.handle_all_keyword()
        res = self.check_valid_gather_subset(self.want.gather_subset)
        if res:
            invalid = ','.join(res)
            raise F5ModuleError(
                "The specified 'gather_subset' options are invalid: {0}".format(invalid)
            )
        result = self.filter_excluded_facts()

        managers = []
        for name in result:
            manager = self.get_manager(name)
            if manager:
                managers.append(manager)

        if not managers:
            result = dict(
                changed=False
            )
            return result

        result = self.execute_managers(managers)
        if result:
            result['changed'] = True
        else:
            result['changed'] = False
        return result

    def filter_excluded_facts(self):
        # Remove the excluded entries from the list of possible facts
        exclude = [x[1:] for x in self.want.gather_subset if x[0] == '!']
        include = [x for x in self.want.gather_subset if x[0] != '!']
        result = [x for x in include if x not in exclude]
        return result

    def handle_all_keyword(self):
        if 'all' not in self.want.gather_subset:
            return
        managers = list(self.managers.keys()) + self.want.gather_subset
        managers.remove('all')
        self.want.update({'gather_subset': managers})

    def check_valid_gather_subset(self, includes):
        """Check that the specified subset is valid

        The ``gather_subset`` parameter is specified as a "raw" field which means that
        any Python type could technically be provided

        :param includes:
        :return:
        """
        keys = self.managers.keys()
        result = []
        for x in includes:
            if x not in keys:
                if x[0] == '!':
                    if x[1:] not in keys:
                        result.append(x)
                else:
                    result.append(x)
        return result

    def execute_managers(self, managers):
        results = dict()
        for manager in managers:
            result = manager.exec_module()
            results.update(result)
        return results

    def get_manager(self, which):
        result = {}
        info = self.managers.get(which, None)
        if not info:
            return result
        kwargs = dict()
        kwargs.update(self.kwargs)

        manager = info.get('manager', None)
        client = info.get('client', None)
        kwargs['client'] = client(**self.module.params)
        result = manager(**kwargs)
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            gather_subset=dict(
                type='list',
                required=True,
                choices=[
                    # Meta choices
                    'all',

                    # Non-meta choices
                    'applications',
                    'managed-devices',
                    'purchased-pool-licenses',
                    'regkey-pools',
                    'system-info',
                    'vlans',

                    # Negations of meta choices
                    '!all',

                    # Negations of non-meta-choices
                    '!applications',
                    '!managed-devices',
                    '!purchased-pool-licenses',
                    '!regkey-pools',
                    '!system-info',
                    '!vlans',
                ]
            ),
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
    if module._name == 'bigiq_device_facts':
        module.deprecate("The 'bigiq_device_facts' module has been renamed to 'bigiq_device_info'", version='2.13')

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
