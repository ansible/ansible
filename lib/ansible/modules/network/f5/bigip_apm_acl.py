#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_apm_acl
short_description: Manage user-defined APM ACLs
description:
  - Manage user-defined APM ACLs.
version_added: 2.9
options:
  name:
    description:
      - Specifies the name of the ACL to manage.
    type: str
    required: True
  description:
    description:
      - User created ACL description.
    type: str
  type:
    description:
      - Specifies the type of ACL to create.
      - Once the type is set it cannot be changed.
    type: str
    choices:
      - static
      - dynamic
  acl_order:
    description:
      - Specifies a number that indicates the order of this ACL relative to other ACLs.
      - When not set, the device will always place the ACL after the last one created.
      - The lower number the higher the ACL will be in the general order, with lowest number C(0) being the topmost one.
      - Valid range of values is between C(0) and C(65535) inclusive.
    type: int
  path_match_case:
    description:
      - Specifies whether alphabetic case is considered when matching paths in an access control entry.
    type: bool
  entries:
    description:
      - Access control entries that define the ACL matching and its respective behavior.
      - The order in which the rules are placed as arguments to this parameter, determines their order in the ACL,
        in other words changing the order of the same elements will cause a change on the unit.
    type: list
    suboptions:
      action:
        description:
          - Specifies the action that the access control entry takes when a match for this access control entry
            is encountered.
        type: str
        required: True
        choices:
          - allow
          - reject
          - discard
          - continue
      dst_port:
        description:
          - Specifies the destination port for the access control entry.
          - Can be set to C(*) to indicate all ports.
          - Parameter is mutually exclusive with C(dst_port_range).
        type: str
      dst_port_range:
        description:
          - Specifies the destination port range for the access control entry.
          - Parameter is mutually exclusive with C(dst_port_range).
          - To indicate all ports the C(dst_port) parameter must be used and set to C(*).
        type: str
      src_port:
        description:
          - Specifies the source port for the access control entry.
          - Can be set to C(*) to indicate all ports.
          - Parameter is mutually exclusive with C(src_port_range).
        type: str
      src_port_range:
        description:
          - Specifies the source port range for the access control entry.
          - Parameter is mutually exclusive with C(src_port_range).
          - To indicate all ports the C(src_port) parameter must be used and set to C(*).
        type: str
      dst_addr:
        description:
          - Specifies the destination IP address for the access control entry.
          - When set to C(any) the ACL will match any destination address, C(dst_mask) is ignored in this case.
        type: str
      dst_mask:
        description:
          - Optional parameter that specifies the destination network mask for the access control entry.
          - If not specified and C(dst_addr) is not C(any) the C(dst_addr) is deemed to be host address.
        type: str
      src_addr:
        description:
          - Specifies the source IP address for the access control entry.
          - When set to C(any) the ACL will match any source address, C(src_mask) is ignored in this case.
        type: str
      src_mask:
        description:
          - Optional parameter that specifies the source network mask for the access control entry.
          - If not specified and C(src_addr) is not C(any) the C(src_addr) is deemed to be host address.
        type: str
      scheme:
        description:
          - This parameter applies to Layer 7 access control entries only.
          - "Specifies the URI scheme: C(http), C(https) or C(any) on which the access control entry operates."
        type: str
        choices:
          - http
          - https
          - any
      protocol:
        description:
          - This parameter applies to Layer 4 access control entries only.
          - "Specifies the protocol: C(tcp), C(udp), C(icmp) or C(all) protocols,
            to which the access control entry applies."
        type: str
        choices:
          - tcp
          - icmp
          - udp
          - all
      host_name:
        description:
          - This parameter applies to Layer 7 access control entries only.
          - Specifies a host to which the access control entry applies.
        type: str
      paths:
        description:
          - This parameter applies to Layer 7 access control entries only.
          - Specifies the path or paths to which the access control entry applies.
        type: str
      log:
        description:
          - Specifies the log level that is logged when actions of this type occur.
          - When C(none) it will log nothing, which is a default action.
          - When C(packet) it will log the matched packet.
        type: str
        choices:
          - none
          - packet
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures that the ACL exists.
      - When C(state) is C(absent), ensures that the ACL is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a static ACL with L4 entries
  bigip_apm_acl:
    name: L4foo
    acl_order: 0
    type: static
    entries:
      - action: allow
        dst_port: '80'
        dst_addr: '192.168.1.1'
        src_port: '443'
        src_addr: '10.10.10.0'
        src_mask: '255.255.255.128'
        protocol: tcp
      - action: reject
        dst_port: '*'
        dst_addr: '192.168.1.1'
        src_port: '*'
        src_addr: '10.10.10.0'
        src_mask: '255.255.255.128'
        protocol: tcp
        log: packet
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a static ACL with L7 entries
  bigip_apm_acl:
    name: L7foo
    acl_order: 1
    type: static
    path_match_case: no
    entries:
      - action: allow
        host_name: 'foobar.com'
        paths: '/shopfront'
        scheme: https
      - action: reject
        host_name: 'internal_foobar.com'
        paths: '/admin'
        scheme: any
        log: packet
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a static ACL with L7/L4 entries
  bigip_apm_acl:
    name: L7L4foo
    acl_order: 2
    type: static
    path_match_case: no
    entries:
      - action: allow
        host_name: 'foobar.com'
        paths: '/shopfront'
        scheme: https
        dst_port: '8181'
        dst_addr: '192.168.1.1'
        protocol: tcp
      - action: reject
        dst_addr: '192.168.1.1'
        host_name: 'internal_foobar.com'
        paths: '/admin'
        scheme: any
        protocol: all
        log: packet
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify a static ACL entries
  bigip_apm_acl:
    name: L4foo
    entries:
      - action: allow
        dst_port: '80'
        dst_addr: '192.168.1.1'
        src_port: '443'
        src_addr: '10.10.10.0'
        src_mask: '255.255.255.128'
        protocol: tcp
      - action: discard
        dst_port: '*'
        dst_addr: 192.168.1.1
        src_port: '*'
        src_addr: '10.10.10.0'
        src_mask: '255.2155.255.128'
        protocol: all
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove static ACL
  bigip_apm_acl:
    name: L4foo
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the ACL.
  returned: changed
  type: str
  sample: My ACL
type:
  description: The type of ACL to create.
  returned: changed
  type: str
  sample: static
acl_order:
  description: The order of this ACL relative to other ACLs.
  returned: changed
  type: int
  sample: 10
path_match_case:
  description: Specifies whether alphabetic case is considered when matching paths in an access control entry.
  returned: changed
  type: bool
  sample: yes
entries:
  description: Access control entries that define the ACL matching and its respective behavior.
  type: complex
  returned: changed
  contains:
    action:
      description: Action that the access control entry takes when a match for this access control entry is encountered.
      returned: changed
      type: str
      sample: allow
    dst_port:
      description: The destination port for the access control entry.
      returned: changed
      type: str
      sample: '80'
    dst_port_range:
      description: The destination port range for the access control entry.
      returned: changed
      type: str
      sample: '80-81'
    src_port:
      description: The source port for the access control entry.
      returned: changed
      type: str
      sample: '80'
    src_port_range:
      description: The source port range for the access control entry.
      returned: changed
      type: str
      sample: '80-81'
    dst_addr:
      description: The destination IP address for the access control entry.
      returned: changed
      type: str
      sample: 192.168.0.1
    dst_mask:
      description: The destination network mask for the access control entry.
      returned: changed
      type: str
      sample: 255.255.255.128
    src_addr:
      description: The source IP address for the access control entry.
      returned: changed
      type: str
      sample: 192.168.0.1
    src_mask:
      description: The source network mask for the access control entry.
      returned: changed
      type: str
      sample: 255.255.255.128
    scheme:
      description: The URI scheme on which the access control entry operates.
      returned: changed
      type: str
      sample: https
    protocol:
      description: The protocol to which the access control entry applies.
      returned: changed
      type: str
      sample: tcp
    host_name:
      description: The host to which the access control entry applies.
      returned: changed
      type: str
      sample: foobar.com
    paths:
      description: The path or paths to which the access control entry applies.
      returned: changed
      type: str
      sample: /fooshop
    log:
      description: The log level that is logged when actions of this type occur.
      returned: changed
      type: str
      sample: packet
  sample: hash/dictionary of values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import is_valid_ip_network
    from library.module_utils.network.f5.ipaddress import is_valid_ip_interface
    from library.module_utils.compat.ipaddress import ip_network
    from library.module_utils.compat.ipaddress import ip_interface
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip_network
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip_interface
    from ansible.module_utils.compat.ipaddress import ip_network
    from ansible.module_utils.compat.ipaddress import ip_interface


class Parameters(AnsibleF5Parameters):
    api_map = {
        'aclOrder': 'acl_order',
        'pathMatchCase': 'path_match_case'
    }

    api_attributes = [
        'entries',
        'description',
        'aclOrder',
        'pathMatchCase',
        'type',
    ]

    returnables = [
        'entries',
        'acl_order',
        'path_match_case',
        'type',
        'description',
    ]

    updatables = [
        'entries',
        'acl_order',
        'path_match_case',
        'type',
        'description',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    protocol_map = {
        'icmp': 1,
        'tcp': 6,
        'udp': 17,
        'all': 0
    }

    @property
    def path_match_case(self):
        result = flatten_boolean(self._values['path_match_case'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'

    @property
    def acl_order(self):
        if self._values['acl_order'] is None:
            return None
        if 0 < self._values['acl_order'] > 65535:
            raise F5ModuleError(
                "Specified number is out of valid range, correct range is between 0 and 65535."
            )
        return self._values['acl_order']

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']

    @property
    def entries(self):
        if self._values['entries'] is None:
            return None
        if self._values['entries'] == 'none':
            return []
        result = []
        element = dict()
        for x in self._values['entries']:
            element['action'] = x['action']
            if 'dst_port' in x and x['dst_port'] is not None:
                if x['dst_port'] == '*':
                    element['dstEndPort'] = 0
                    element['dstStartPort'] = 0
                else:
                    self._validate_port(int(x['dst_port']))
                    element['dstEndPort'] = int(x['dst_port'])
                    element['dstStartPort'] = int(x['dst_port'])
            if 'dst_port_range' in x and x['dst_port_range'] is not None:
                start, stop = self._validate_ports(x['dst_port_range'])
                element['dstEndPort'] = stop
                element['dstStartPort'] = start
            if 'src_port' in x and x['src_port'] is not None:
                if x['src_port'] == '*':
                    element['srcEndPort'] = 0
                    element['srcStartPort'] = 0
                else:
                    self._validate_port(int(x['src_port']))
                    element['srcEndPort'] = int(x['src_port'])
                    element['srcStartPort'] = int(x['src_port'])
            if 'src_port_range' in x and x['src_port_range'] is not None:
                start, stop = self._validate_ports(x['src_port_range'])
                element['srcEndPort'] = stop
                element['srcStartPort'] = start
            if 'dst_addr' in x and x['dst_addr'] is not None:
                if 'dst_mask' in x and x['dst_mask'] is not None:
                    element['dstSubnet'] = self._convert_address(x['dst_addr'], x['dst_mask'])
                else:
                    element['dstSubnet'] = self._convert_address(x['dst_addr'])
            if 'src_addr' in x and x['src_addr'] is not None:
                if 'src_mask' in x and x['src_mask'] is not None:
                    element['srcSubnet'] = self._convert_address(x['src_addr'], x['src_mask'])
                else:
                    element['srcSubnet'] = self._convert_address(x['src_addr'])
            if 'scheme' in x and x['scheme'] is not None:
                element['scheme'] = x['scheme']
            if 'protocol' in x and x['protocol'] is not None:
                element['protocol'] = self.protocol_map[x['protocol']]
            if 'host_name' in x and x['host_name'] is not None:
                element['host'] = x['host_name']
            if 'paths' in x and x['paths'] is not None:
                element['paths'] = x['paths']
            if 'log' in x and x['log'] is not None:
                element['log'] = x['log']
            result.append(element)
        return result

    def _validate_port(self, item):
        if 0 < item > 65535:
            raise F5ModuleError(
                "Specified port number is out of valid range, correct range is between 0 and 65535."
            )

    def _validate_ports(self, item):
        start, stop = item.split('-')
        start = int(start.strip())
        stop = int(stop.strip())
        if 0 < start > 65535 or 0 < stop > 65535:
            raise F5ModuleError(
                "Specified port number is out of valid range, correct range is between 0 and 65535."
            )
        return start, stop

    def _convert_address(self, item, mask=None):
        if item == 'any':
            return '0.0.0.0/0'
        if not is_valid_ip(item):
            raise F5ModuleError('The provided IP address is not a valid IP address.')
        if mask:
            msk = self._convert_netmask(mask)
            network = '{0}/{1}'.format(item, msk)
            if is_valid_ip_network(u'{0}'.format(network)):
                return network
            else:
                raise F5ModuleError(
                    'The provided IP and Mask are not a valid IP network.'
                )
        host = ip_interface(u'{0}'.format(item))
        return host.with_prefixlen

    def _convert_netmask(self, item):
        result = -1
        try:
            result = int(item)
            if 0 < result < 256:
                pass
        except ValueError:
            if is_valid_ip(item):
                ip = ip_network(u'0.0.0.0/%s' % str(item))
                result = ip.prefixlen
        if result < 0:
            raise F5ModuleError(
                'The provided netmask {0} is neither in IP or CIDR format'.format(result)
            )
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    protocol_map = {
        1: 'icmp',
        6: 'tcp',
        17: 'udp',
        0: 'all'
    }

    @property
    def path_match_case(self):
        result = flatten_boolean(self._values['path_match_case'])
        return result

    @property
    def entries(self):
        if self._values['entries'] is None:
            return None
        if not self._values['entries']:
            return 'none'
        result = []
        to_filter = dict()
        for x in self._values['entries']:
            to_filter['action'] = x['action']
            if 'dstStartPort' and 'dstEndPort' in x:
                if x['dstStartPort'] == x['dstEndPort']:
                    if x['dstStartPort'] == 0:
                        to_filter['dst_port'] = '*'
                    else:
                        to_filter['dst_port'] = str(x['dstStartPort'])
                else:
                    to_filter['dst_port_range'] = '{0}-{1}'.format(x['dstStartPort'], x['dstEndPort'])
            if 'srcStartPort' and 'srcEndPort' in x:
                if x['srcStartPort'] == x['srcEndPort']:
                    if x['srcStartPort'] == 0:
                        to_filter['src_port'] = '*'
                    else:
                        to_filter['src_port'] = str(x['srcStartPort'])
                else:
                    to_filter['src_port_range'] = '{0}-{1}'.format(x['srcStartPort'], x['srcEndPort'])
            if 'dstSubnet' in x:
                to_filter['dst_addr'], to_filter['dst_mask'] = self._convert_address(x['dstSubnet'])
            if 'srcSubnet' in x:
                to_filter['src_addr'], to_filter['src_mask'] = self._convert_address(x['srcSubnet'])
            if 'scheme' in x:
                to_filter['scheme'] = x['scheme']
            if 'protocol' in x:
                to_filter['protocol'] = self.protocol_map[x['protocol']]
            if 'host' in x:
                to_filter['host_name'] = x['host']
            if 'paths' in x:
                to_filter['paths'] = x['paths']
            if 'log' in x:
                to_filter['log'] = x['log']
            element = self._filter_params(to_filter)
            result.append(element)
        return result

    def _convert_address(self, item):
        if item == '0.0.0.0/0':
            return 'any', None
        result = ip_network(u'{0}'.format(item))
        if result.prefixlen == 32:
            return str(result.network_address), None
        else:
            return str(result.network_address), str(result.netmask)


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
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def entries(self):
        if self.want.entries is None:
            return None
        if self.have.entries is None and self.want.entries == []:
            return None

        want = self.want.entries
        have = list()
        # First we remove extra keys in have
        for idx, item in enumerate(want):
            entry = self._filter_have(item, self.have.entries[idx])
            have.append(entry)
        # Compare each element in the list by position
        for idx, item in enumerate(want):
            if item != have[idx]:
                return self.want.entries

    def _filter_have(self, want, have):
        to_check = set(want.keys()).intersection(set(have.keys()))
        result = dict()
        for k in list(to_check):
            result[k] = have[k]
        return result

    @property
    def type(self):
        if self.want.type is None:
            return None
        if self.want.type == self.have.type:
            return None
        raise F5ModuleError(
            "ACL type cannot be changed after ACL creation."
        )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/apm/acl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/apm/acl/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/apm/acl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/apm/acl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/apm/acl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            acl_order=dict(type='int'),
            description=dict(),
            path_match_case=dict(type='bool'),
            type=dict(
                choices=['static', 'dynamic'],
            ),
            entries=dict(
                type='list',
                elements='dict',
                options=dict(
                    action=dict(
                        choices=['allow', 'reject', 'discard', 'continue'],
                        required=True
                    ),
                    dst_port=dict(),
                    dst_port_range=dict(),
                    src_port=dict(),
                    src_port_range=dict(),
                    dst_addr=dict(),
                    dst_mask=dict(),
                    src_addr=dict(),
                    src_mask=dict(),
                    scheme=dict(
                        choices=['any', 'https', 'http']
                    ),
                    protocol=dict(
                        choices=['tcp', 'icmp', 'udp', 'all']
                    ),
                    host_name=dict(),
                    paths=dict(),
                    log=dict(
                        choices=['packet', 'none']
                    ),
                ),
                mutually_exclusive=[
                    ['dst_port', 'dst_port_range'],
                    ['src_port', 'src_port_range'],
                ],
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
