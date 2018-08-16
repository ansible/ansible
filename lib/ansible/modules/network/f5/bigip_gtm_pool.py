#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_gtm_pool
short_description: Manages F5 BIG-IP GTM pools
description:
    - Manages F5 BIG-IP GTM pools.
version_added: 2.4
options:
  state:
    description:
      - Pool state. When C(present), ensures that the pool is created and enabled.
        When C(absent), ensures that the pool is removed from the system. When
        C(enabled) or C(disabled), ensures that the pool is enabled or disabled
        (respectively) on the remote device.
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
  preferred_lb_method:
    description:
      - The load balancing mode that the system tries first.
    choices:
      - round-robin
      - return-to-dns
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - least-connections
      - lowest-round-trip-time
      - fewest-hops
      - packet-rate
      - cpu
      - completion-rate
      - quality-of-service
      - kilobytes-per-second
      - drop-packet
      - fallback-ip
      - virtual-server-score
  alternate_lb_method:
    description:
      - The load balancing mode that the system tries if the
        C(preferred_lb_method) is unsuccessful in picking a pool.
    choices:
      - round-robin
      - return-to-dns
      - none
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - packet-rate
      - drop-packet
      - fallback-ip
      - virtual-server-score
  fallback_lb_method:
    description:
      - The load balancing mode that the system tries if both the
        C(preferred_lb_method) and C(alternate_lb_method)s are unsuccessful
        in picking a pool.
    choices:
      - round-robin
      - return-to-dns
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - least-connections
      - lowest-round-trip-time
      - fewest-hops
      - packet-rate
      - cpu
      - completion-rate
      - quality-of-service
      - kilobytes-per-second
      - drop-packet
      - fallback-ip
      - virtual-server-score
      - none
  fallback_ip:
    description:
      - Specifies the IPv4, or IPv6 address of the server to which the system
        directs requests when it cannot use one of its pools to do so.
        Note that the system uses the fallback IP only if you select the
        C(fallback_ip) load balancing method.
  type:
    description:
      - The type of GTM pool that you want to create. On BIG-IP releases
        prior to version 12, this parameter is not required. On later versions
        of BIG-IP, this is a required parameter.
    choices:
      - a
      - aaaa
      - cname
      - mx
      - naptr
      - srv
  name:
    description:
      - Name of the GTM pool.
    required: True
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  members:
    description:
      - Members to assign to the pool.
      - The order of the members in this list is the order that they will be listed in the pool.
    suboptions:
      server:
        description:
          - Name of the server which the pool member is a part of.
        required: True
      virtual_server:
        description:
          - Name of the virtual server, associated with the server, that the pool member is a part of.
        required: True
    version_added: 2.6
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to monitor this resource.
      - When C(availability_requirements.type) is C(require), you may only have a single monitor in the
        C(monitors) list.
    version_added: 2.6
  availability_requirements:
    description:
      - Specifies, if you activate more than one health monitor, the number of health
        monitors that must receive successful responses in order for the link to be
        considered available.
    suboptions:
      type:
        description:
          - Monitor rule type when C(monitors) is specified.
          - When creating a new pool, if this value is not specified, the default of 'all' will be used.
        choices: ['all', 'at_least', 'require']
      at_least:
        description:
          - Specifies the minimum number of active health monitors that must be successful
            before the link is considered up.
          - This parameter is only relevant when a C(type) of C(at_least) is used.
          - This parameter will be ignored if a type of either C(all) or C(require) is used.
      number_of_probes:
        description:
          - Specifies the minimum number of probes that must succeed for this server to be declared up.
          - When creating a new virtual server, if this parameter is specified, then the C(number_of_probers)
            parameter must also be specified.
          - The value of this parameter should always be B(lower) than, or B(equal to), the value of C(number_of_probers).
          - This parameter is only relevant when a C(type) of C(require) is used.
          - This parameter will be ignored if a type of either C(all) or C(at_least) is used.
      number_of_probers:
        description:
          - Specifies the number of probers that should be used when running probes.
          - When creating a new virtual server, if this parameter is specified, then the C(number_of_probes)
            parameter must also be specified.
          - The value of this parameter should always be B(higher) than, or B(equal to), the value of C(number_of_probers).
          - This parameter is only relevant when a C(type) of C(require) is used.
          - This parameter will be ignored if a type of either C(all) or C(at_least) is used.
    version_added: 2.6
notes:
  - Requires the netaddr Python package on the host. This is as easy as
    pip install netaddr.
extends_documentation_fragment: f5
requirements:
  - netaddr
author:
  - Tim Rupp (@caphrim007)
'''

RETURN = r'''
preferred_lb_method:
  description: New preferred load balancing method for the pool.
  returned: changed
  type: string
  sample: topology
alternate_lb_method:
  description: New alternate load balancing method for the pool.
  returned: changed
  type: string
  sample: drop-packet
fallback_lb_method:
  description: New fallback load balancing method for the pool.
  returned: changed
  type: string
  sample: fewest-hops
fallback_ip:
  description: New fallback IP used when load balacing using the C(fallback_ip) method.
  returned: changed
  type: string
  sample: 10.10.10.10
monitors:
  description: The new list of monitors for the resource.
  returned: changed
  type: list
  sample: ['/Common/monitor1', '/Common/monitor2']
members:
  description: List of members in the pool.
  returned: changed
  type: complex
  contains:
    server:
      description: The name of the server portion of the member.
      returned: changed
      type: string
    virtual_server:
      description: The name of the virtual server portion of the member.
      returned: changed
      type: string
'''

EXAMPLES = r'''
- name: Create a GTM pool
  bigip_gtm_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_pool
  delegate_to: localhost

- name: Disable pool
  bigip_gtm_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: disabled
    name: my_pool
  delegate_to: localhost
'''

import copy
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.sdk_exception import LazyAttributesRequired
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.sdk_exception import LazyAttributesRequired
    except ImportError:
        HAS_F5SDK = False

try:
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'loadBalancingMode': 'preferred_lb_method',
        'alternateMode': 'alternate_lb_method',
        'fallbackMode': 'fallback_lb_method',
        'verifyMemberAvailability': 'verify_member_availability',
        'fallbackIpv4': 'fallback_ip',
        'fallbackIpv6': 'fallback_ip',
        'fallbackIp': 'fallback_ip',
        'membersReference': 'members',
        'monitor': 'monitors'
    }

    updatables = [
        'alternate_lb_method',
        'fallback_ip',
        'fallback_lb_method',
        'members',
        'monitors',
        'preferred_lb_method',
        'state',
    ]

    returnables = [
        'alternate_lb_method',
        'fallback_ip',
        'fallback_lb_method',
        'members',
        'monitors',
        'preferred_lb_method',
        'enabled',
        'disabled'
    ]

    api_attributes = [
        'alternateMode',
        'disabled',
        'enabled',
        'fallbackIp',
        'fallbackIpv4',
        'fallbackIpv6',
        'fallbackMode',
        'loadBalancingMode',
        'members',
        'verifyMemberAvailability',
        # The monitor attribute is not included here, because it can break the
        # API calls to the device. If this bug is ever fixed, uncomment this code.
        #
        # monitor
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    @property
    def collection(self):
        type_map = dict(
            a='a_s',
            aaaa='aaaas',
            cname='cnames',
            mx='mxs',
            naptr='naptrs',
            srv='srvs'
        )
        if self._values['type'] is None:
            return None
        wideip_type = self._values['type']
        return type_map[wideip_type]

    @property
    def type(self):
        if self._values['type'] is None:
            return None
        return str(self._values['type'])

    @property
    def verify_member_availability(self):
        if self._values['verify_member_availability'] is None:
            return None
        elif self._values['verify_member_availability']:
            return 'enabled'
        else:
            return 'disabled'

    @property
    def fallback_ip(self):
        if self._values['fallback_ip'] is None:
            return None
        if self._values['fallback_ip'] == 'any':
            return 'any'
        if self._values['fallback_ip'] == 'any6':
            return 'any6'
        try:
            address = IPAddress(self._values['fallback_ip'])
            if address.version == 4:
                return str(address.ip)
            elif address.version == 6:
                return str(address.ip)
            return None
        except AddrFormatError:
            raise F5ModuleError(
                'The provided fallback address is not a valid IPv4 address'
            )

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']

    @property
    def enabled(self):
        if self._values['enabled'] is None:
            return None
        return True

    @property
    def disabled(self):
        if self._values['disabled'] is None:
            return None
        return True


class ApiParameters(Parameters):
    @property
    def members(self):
        result = []
        if self._values['members'] is None or 'items' not in self._values['members']:
            return []
        for item in self._values['members']['items']:
            result.append(dict(item=item['fullPath'], order=item['memberOrder']))
        result = [x['item'] for x in sorted(result, key=lambda k: k['order'])]
        return result

    @property
    def availability_requirement_type(self):
        if self._values['monitors'] is None:
            return None
        if 'min ' in self._values['monitors']:
            return 'at_least'
        elif 'require ' in self._values['monitors']:
            return 'require'
        else:
            return 'all'

    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            result.sort()
            return result
        except Exception:
            return self._values['monitors']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        if self._values['monitors'] == 'default':
            return 'default'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        elif self.availability_requirement_type == 'require':
            monitors = ' '.join(monitors)
            result = 'require {0} from {1} {{ {2} }}'.format(self.number_of_probes, self.number_of_probers, monitors)
        else:
            result = ' and '.join(monitors).strip()

        return result

    @property
    def number_of_probes(self):
        """Returns the probes value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probes" value that can be updated in the module.

        Returns:
             int: The probes value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+(?P<probes>\d+)\s+from'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('probes')

    @property
    def number_of_probers(self):
        """Returns the probers value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probers" value that can be updated in the module.

        Returns:
             int: The probers value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+\d+\s+from\s+(?P<probers>\d+)\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('probers')

    @property
    def at_least(self):
        """Returns the 'at least' value from the monitor string.

        The monitor string for a Require monitor looks like this.

            min 1 of { /Common/gateway_icmp }

        This method parses out the first of the numeric values. This values represents
        the "at_least" value that can be updated in the module.

        Returns:
             int: The at_least value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+(?P<least>\d+)\s+of\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('least')


class ModuleParameters(Parameters):
    def _get_availability_value(self, type):
        if self._values['availability_requirements'] is None:
            return None
        if self._values['availability_requirements'][type] is None:
            return None
        return int(self._values['availability_requirements'][type])

    @property
    def members(self):
        if self._values['members'] is None:
            return None
        if len(self._values['members']) == 1 and self._values['members'][0] == '':
            return []
        result = []
        for member in self._values['members']:
            if 'server' not in member:
                raise F5ModuleError(
                    "One of the provided members is missing a 'server' sub-option."
                )
            if 'virtual_server' not in member:
                raise F5ModuleError(
                    "One of the provided members is missing a 'virtual_server' sub-option."
                )
            name = '{0}:{1}'.format(member['server'], member['virtual_server'])
            name = fq_name(self.partition, name)
            if name in result:
                continue
            result.append(name)
        result = list(result)
        return result

    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            result.sort()
            return result
        except Exception:
            return self._values['monitors']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        if len(self._values['monitors']) == 1 and self._values['monitors'][0] == '':
            return 'default'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            if self.at_least > len(self.monitors_list):
                raise F5ModuleError(
                    "The 'at_least' value must not exceed the number of 'monitors'."
                )
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        elif self.availability_requirement_type == 'require':
            monitors = ' '.join(monitors)
            if self.number_of_probes > self.number_of_probers:
                raise F5ModuleError(
                    "The 'number_of_probes' must not exceed the 'number_of_probers'."
                )
            result = 'require {0} from {1} {{ {2} }}'.format(self.number_of_probes, self.number_of_probers, monitors)
        else:
            result = ' and '.join(monitors).strip()

        return result

    @property
    def availability_requirement_type(self):
        if self._values['availability_requirements'] is None:
            return None
        return self._values['availability_requirements']['type']

    @property
    def number_of_probes(self):
        return self._get_availability_value('number_of_probes')

    @property
    def number_of_probers(self):
        return self._get_availability_value('number_of_probers')

    @property
    def at_least(self):
        return self._get_availability_value('at_least')


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        return self._values['monitors']

    @property
    def members(self):
        results = []
        if self._values['members'] is None:
            return None
        for idx, member in enumerate(self._values['members']):
            result = dict(
                name=member,
                memberOrder=idx
            )
            results.append(result)
        return results


class ReportableChanges(Changes):
    @property
    def members(self):
        results = []
        if self._values['members'] is None:
            return None
        for member in self._values['members']:
            parts = member.split(':')
            results.append(dict(
                server=fq_name(self.partition, parts[0]),
                virtual_server=fq_name(self.partition, parts[1])
            ))
        return results


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def state(self):
        if self.want.state == 'disabled' and self.have.enabled:
            return dict(
                disabled=True
            )
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            return dict(
                enabled=True
            )

    @property
    def monitors(self):
        if self.want.monitors is None:
            return None
        if self.want.monitors == 'default' and self.have.monitors == 'default':
            return None
        if self.want.monitors == 'default' and self.have.monitors is None:
            return None
        if self.want.monitors == 'default' and len(self.have.monitors) > 0:
            return 'default'
        if self.have.monitors is None:
            return self.want.monitors
        if self.have.monitors != self.want.monitors:
            return self.want.monitors


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.client = kwargs.get('client', None)

    def exec_module(self):
        if not self.gtm_provisioned():
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'typed':
            return TypedManager(**self.kwargs)
        elif type == 'untyped':
            return UntypedManager(**self.kwargs)

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
            return True
        else:
            return False

    def gtm_provisioned(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name='provisioned.cpu.gtm'
        )
        if int(resource.value) == 0:
            return False
        return True


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ["present", "disabled"]:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def create(self):
        if self.want.state == 'disabled':
            self.want.update({'disabled': True})
        elif self.want.state in ['present', 'enabled']:
            self.want.update({'enabled': True})

        self._set_changed_options()

        if self.want.availability_requirement_type == 'require' and len(self.want.monitors_list) > 1:
            raise F5ModuleError(
                "Only one monitor may be specified when using an availability_requirement type of 'require'"
            )

        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the GTM pool")

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the GTM pool")
        return True

    def update_monitors_on_device(self):
        """Updates the monitors string on a virtual server

        There is a long-standing bug in GTM virtual servers where the monitor value
        is a string that includes braces. These braces cause the REST API to panic and
        fail to update or create any resources that have an "at_least" or "require"
        set of availability_requirements.

        This method exists to do a tmsh command to cause the update to take place on
        the device.

        Preferably, this method can be removed and the bug be fixed. The API should
        be working, obviously, but the more concerning issue is if tmsh commands change
        over time, breaking this method.
        """
        command = 'tmsh modify gtm pool {0} /{1}/{2} monitor {3}'.format(
            self.want.type, self.want.partition, self.want.name, self.want.monitors
        )
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(command)
        )
        try:
            if hasattr(output, 'commandResult'):
                if len(output.commandResult.strip()) > 0:
                    raise F5ModuleError(output.commandResult)
        except (AttributeError, NameError, LazyAttributesRequired):
            pass
        return True


class TypedManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(TypedManager, self).__init__(**kwargs)
        if self.want.type is None:
            raise F5ModuleError(
                "The 'type' option is required for BIG-IP instances "
                "greater than or equal to 12.x"
            )

    def present(self):
        types = [
            'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
        ]
        if self.want.type is None:
            raise F5ModuleError(
                "A pool 'type' must be specified"
            )
        elif self.want.type not in types:
            raise F5ModuleError(
                "The specified pool type is invalid"
            )

        return super(TypedManager, self).present()

    def exists(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.changes.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if params:
            result.modify(**params)
        if self.want.monitors:
            self.update_monitors_on_device()

    def read_current_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition,
            requests_params=dict(
                params=dict(
                    expandSubcollections='true'
                )
            )
        )
        result = result.attrs
        return ApiParameters(params=result)

    def create_on_device(self):
        params = self.changes.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )
        if self.want.monitors:
            self.update_monitors_on_device()

    def remove_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()


class UntypedManager(BaseManager):
    def exists(self):
        result = self.client.api.tm.gtm.pools.pool.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)
        if self.want.monitors:
            self.update_monitors_on_device()

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.gtm.pools.pool.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )
        if self.want.monitors:
            self.update_monitors_on_device()

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.states = ['absent', 'present', 'enabled', 'disabled']
        self.preferred_lb_methods = [
            'round-robin', 'return-to-dns', 'ratio', 'topology',
            'static-persistence', 'global-availability',
            'virtual-server-capacity', 'least-connections',
            'lowest-round-trip-time', 'fewest-hops', 'packet-rate', 'cpu',
            'completion-rate', 'quality-of-service', 'kilobytes-per-second',
            'drop-packet', 'fallback-ip', 'virtual-server-score'
        ]
        self.alternate_lb_methods = [
            'round-robin', 'return-to-dns', 'none', 'ratio', 'topology',
            'static-persistence', 'global-availability',
            'virtual-server-capacity', 'packet-rate', 'drop-packet',
            'fallback-ip', 'virtual-server-score'
        ]
        self.fallback_lb_methods = copy.copy(self.preferred_lb_methods)
        self.fallback_lb_methods.append('none')
        self.types = [
            'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
        ]
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            state=dict(
                default='present',
                choices=self.states,
            ),
            preferred_lb_method=dict(
                choices=self.preferred_lb_methods,
            ),
            fallback_lb_method=dict(
                choices=self.fallback_lb_methods,
            ),
            alternate_lb_method=dict(
                choices=self.alternate_lb_methods,
            ),
            fallback_ip=dict(),
            type=dict(
                choices=self.types
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            members=dict(
                type='list',
                options=dict(
                    server=dict(required=True),
                    virtual_server=dict(required=True)
                )
            ),
            availability_requirements=dict(
                type='dict',
                options=dict(
                    type=dict(
                        choices=['all', 'at_least', 'require'],
                        required=True
                    ),
                    at_least=dict(type='int'),
                    number_of_probes=dict(type='int'),
                    number_of_probers=dict(type='int')
                ),
                mutually_exclusive=[
                    ['at_least', 'number_of_probes'],
                    ['at_least', 'number_of_probers'],
                ],
                required_if=[
                    ['type', 'at_least', ['at_least']],
                    ['type', 'require', ['number_of_probes', 'number_of_probers']]
                ]
            ),
            monitors=dict(type='list'),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['preferred_lb_method', 'fallback-ip', ['fallback_ip']],
            ['fallback_lb_method', 'fallback-ip', ['fallback_ip']],
            ['alternate_lb_method', 'fallback-ip', ['fallback_ip']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")
    if not HAS_NETADDR:
        module.fail_json(msg="The python netaddr module is required")

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
