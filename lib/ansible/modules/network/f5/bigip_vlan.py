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
module: bigip_vlan
short_description: Manage VLANs on a BIG-IP system
description:
  - Manage VLANs on a BIG-IP system
version_added: 2.2
options:
  description:
    description:
      - The description to give to the VLAN.
  tagged_interfaces:
    description:
      - Specifies a list of tagged interfaces and trunks that you want to
        configure for the VLAN. Use tagged interfaces or trunks when
        you want to assign a single interface or trunk to multiple VLANs.
    aliases:
      - tagged_interface
  untagged_interfaces:
    description:
      - Specifies a list of untagged interfaces and trunks that you want to
        configure for the VLAN.
    aliases:
      - untagged_interface
  name:
    description:
      - The VLAN to manage. If the special VLAN C(ALL) is specified with
        the C(state) value of C(absent) then all VLANs will be removed.
    required: True
  state:
    description:
      - The state of the VLAN on the system. When C(present), guarantees
        that the VLAN exists with the provided attributes. When C(absent),
        removes the VLAN from the system.
    default: present
    choices:
      - absent
      - present
  tag:
    description:
      - Tag number for the VLAN. The tag number can be any integer between 1
        and 4094. The system automatically assigns a tag number if you do not
        specify a value.
  mtu:
    description:
      - Specifies the maximum transmission unit (MTU) for traffic on this VLAN.
        When creating a new VLAN, if this parameter is not specified, the default
        value used will be C(1500).
      - This number must be between 576 to 9198.
    version_added: 2.5
  cmp_hash:
    description:
      - Specifies how the traffic on the VLAN will be disaggregated. The value
        selected determines the traffic disaggregation method. You can choose to
        disaggregate traffic based on C(source-address) (the source IP address),
        C(destination-address) (destination IP address), or C(default), which
        specifies that the default CMP hash uses L4 ports.
      - When creating a new VLAN, if this parameter is not specified, the default
        of C(default) is used.
    choices:
      - default
      - destination-address
      - source-address
      - dst-ip
      - src-ip
      - dest
      - destination
      - source
      - dst
      - src
    version_added: 2.5
  dag_tunnel:
    description:
      - Specifies how the disaggregator (DAG) distributes received tunnel-encapsulated
        packets to TMM instances. Select C(inner) to distribute packets based on information
        in inner headers. Select C(outer) to distribute packets based on information in
        outer headers without inspecting inner headers.
      - When creating a new VLAN, if this parameter is not specified, the default
        of C(outer) is used.
      - This parameter is not supported on Virtual Editions of BIG-IP.
    version_added: 2.5
    choices:
      - inner
      - outer
  dag_round_robin:
    description:
      - Specifies whether some of the stateless traffic on the VLAN should be
        disaggregated in a round-robin order instead of using a static hash. The
        stateless traffic includes non-IP L2 traffic, ICMP, some UDP protocols,
        and so on.
      - When creating a new VLAN, if this parameter is not specified, the default
        of (no) is used.
    version_added: 2.5
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - Requires BIG-IP versions >= 12.0.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create VLAN
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Set VLAN tag
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 2345 as tagged to interface 1.1
  bigip_vlan:
      tagged_interface: 1.1
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 1234 as tagged to interfaces 1.1 and 1.2
  bigip_vlan:
      tagged_interfaces:
          - 1.1
          - 1.2
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "1234"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The description set on the VLAN.
  returned: changed
  type: string
  sample: foo VLAN
interfaces:
  description: Interfaces that the VLAN is assigned to.
  returned: changed
  type: list
  sample: ['1.1','1.2']
partition:
  description: The partition that the VLAN was created on.
  returned: changed
  type: string
  sample: Common
tag:
  description: The ID of the VLAN.
  returned: changed
  type: int
  sample: 2345
cmp_hash:
  description: New traffic disaggregation method.
  returned: changed
  type: string
  sample: source-address
dag_tunnel:
  description: The new DAG tunnel setting.
  returned: changed
  type: string
  sample: outer
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
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
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'cmpHash': 'cmp_hash',
        'dagTunnel': 'dag_tunnel',
        'dagRoundRobin': 'dag_round_robin'
    }

    updatables = [
        'tagged_interfaces', 'untagged_interfaces', 'tag',
        'description', 'mtu', 'cmp_hash', 'dag_tunnel',
        'dag_round_robin'
    ]

    returnables = [
        'description', 'partition', 'tag', 'interfaces',
        'tagged_interfaces', 'untagged_interfaces', 'mtu',
        'cmp_hash', 'dag_tunnel', 'dag_round_robin'
    ]

    api_attributes = [
        'description', 'interfaces', 'tag', 'mtu', 'cmpHash',
        'dagTunnel', 'dagRoundRobin'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class ApiParameters(Parameters):
    @property
    def tagged_interfaces(self):
        if self._values['interfaces'] is None:
            return None
        result = [str(x.name) for x in self._values['interfaces'] if x.tagged is True]
        result = sorted(result)
        return result

    @property
    def untagged_interfaces(self):
        if self._values['interfaces'] is None:
            return None
        result = [str(x.name) for x in self._values['interfaces'] if x.untagged is True]
        result = sorted(result)
        return result


class ModuleParameters(Parameters):
    @property
    def untagged_interfaces(self):
        if self._values['untagged_interfaces'] is None:
            return None
        if self._values['untagged_interfaces'] is None:
            return None
        if len(self._values['untagged_interfaces']) == 1 and self._values['untagged_interfaces'][0] == '':
            return ''
        result = sorted([str(x) for x in self._values['untagged_interfaces']])
        return result

    @property
    def tagged_interfaces(self):
        if self._values['tagged_interfaces'] is None:
            return None
        if self._values['tagged_interfaces'] is None:
            return None
        if len(self._values['tagged_interfaces']) == 1 and self._values['tagged_interfaces'][0] == '':
            return ''
        result = sorted([str(x) for x in self._values['tagged_interfaces']])
        return result

    @property
    def mtu(self):
        if self._values['mtu'] is None:
            return None
        if int(self._values['mtu']) < 576 or int(self._values['mtu']) > 9198:
            raise F5ModuleError(
                "The mtu value must be between 576 - 9198"
            )
        return int(self._values['mtu'])

    @property
    def cmp_hash(self):
        if self._values['cmp_hash'] is None:
            return None
        if self._values['cmp_hash'] in ['source-address', 'src', 'src-ip', 'source']:
            return 'src-ip'
        if self._values['cmp_hash'] in ['destination-address', 'dest', 'dst-ip', 'destination', 'dst']:
            return 'dst-ip'
        else:
            return 'default'

    @property
    def dag_round_robin(self):
        if self._values['dag_round_robin'] is None:
            return None
        if self._values['dag_round_robin'] is True:
            return 'enabled'
        else:
            return 'disabled'


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
    @property
    def tagged_interfaces(self):
        if self._values['interfaces'] is None:
            return None
        result = [str(x['name']) for x in self._values['interfaces'] if 'tagged' in x and x['tagged'] is True]
        result = sorted(result)
        return result

    @property
    def untagged_interfaces(self):
        if self._values['interfaces'] is None:
            return None
        result = [str(x['name']) for x in self._values['interfaces'] if 'untagged' in x and x['untagged'] is True]
        result = sorted(result)
        return result


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
    def untagged_interfaces(self):
        result = []
        if self.want.untagged_interfaces is None:
            return None
        elif self.want.untagged_interfaces == '' and self.have.untagged_interfaces is None:
            return None
        elif self.want.untagged_interfaces == '' and len(self.have.untagged_interfaces) > 0:
            pass
        elif not self.have.untagged_interfaces:
            result = dict(
                interfaces=[dict(name=x, untagged=True) for x in self.want.untagged_interfaces]
            )
        elif set(self.want.untagged_interfaces) != set(self.have.untagged_interfaces):
            result = dict(
                interfaces=[dict(name=x, untagged=True) for x in self.want.untagged_interfaces]
            )
        else:
            return None
        return result

    @property
    def tagged_interfaces(self):
        result = []
        if self.want.tagged_interfaces is None:
            return None
        elif self.want.tagged_interfaces == '' and self.have.tagged_interfaces is None:
            return None
        elif self.want.tagged_interfaces == '' and len(self.have.tagged_interfaces) > 0:
            pass
        elif not self.have.tagged_interfaces:
            result = dict(
                interfaces=[dict(name=x, tagged=True) for x in self.want.tagged_interfaces]
            )
        elif set(self.want.tagged_interfaces) != set(self.have.tagged_interfaces):
            result = dict(
                interfaces=[dict(name=x, tagged=True) for x in self.want.tagged_interfaces]
            )
        else:
            return None
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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
            if state == "present":
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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the VLAN")
        return True

    def create(self):
        self.have = ApiParameters()
        if self.want.mtu is None:
            self.want.update({'mtu': 1500})
        self._update_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.net.vlans.vlan.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def exists(self):
        return self.client.api.tm.net.vlans.vlan.exists(
            name=self.want.name,
            partition=self.want.partition
        )

    def remove_from_device(self):
        resource = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name, partition=self.want.partition
        )
        interfaces = resource.interfaces_s.get_collection()
        result = resource.attrs
        result['interfaces'] = interfaces
        return ApiParameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True,
            ),
            tagged_interfaces=dict(
                type='list',
                aliases=['tagged_interface']
            ),
            untagged_interfaces=dict(
                type='list',
                aliases=['untagged_interface']
            ),
            description=dict(),
            tag=dict(
                type='int'
            ),
            mtu=dict(type='int'),
            cmp_hash=dict(
                choices=[
                    'default',
                    'destination-address', 'dest', 'dst-ip', 'destination', 'dst',
                    'source-address', 'src', 'src-ip', 'source'
                ]
            ),
            dag_tunnel=dict(
                choices=['inner', 'outer']
            ),
            dag_round_robin=dict(type='bool'),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['tagged_interfaces', 'untagged_interfaces']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
