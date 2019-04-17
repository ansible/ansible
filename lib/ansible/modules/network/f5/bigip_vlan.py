#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

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
    type: str
  tagged_interfaces:
    description:
      - Specifies a list of tagged interfaces and trunks that you want to
        configure for the VLAN. Use tagged interfaces or trunks when
        you want to assign a single interface or trunk to multiple VLANs.
      - This parameter is mutually exclusive with the C(untagged_interfaces)
        and C(interfaces) parameters.
    type: list
    aliases:
      - tagged_interface
  untagged_interfaces:
    description:
      - Specifies a list of untagged interfaces and trunks that you want to
        configure for the VLAN.
      - This parameter is mutually exclusive with the C(tagged_interfaces)
        and C(interfaces) parameters.
    type: list
    aliases:
      - untagged_interface
  name:
    description:
      - The VLAN to manage. If the special VLAN C(ALL) is specified with
        the C(state) value of C(absent) then all VLANs will be removed.
    type: str
    required: True
  state:
    description:
      - The state of the VLAN on the system. When C(present), guarantees
        that the VLAN exists with the provided attributes. When C(absent),
        removes the VLAN from the system.
    type: str
    choices:
      - absent
      - present
    default: present
  tag:
    description:
      - Tag number for the VLAN. The tag number can be any integer between 1
        and 4094. The system automatically assigns a tag number if you do not
        specify a value.
    type: int
  mtu:
    description:
      - Specifies the maximum transmission unit (MTU) for traffic on this VLAN.
        When creating a new VLAN, if this parameter is not specified, the default
        value used will be C(1500).
      - This number must be between 576 to 9198.
    type: int
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
    type: str
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
    type: str
    choices:
      - inner
      - outer
    version_added: 2.5
  dag_round_robin:
    description:
      - Specifies whether some of the stateless traffic on the VLAN should be
        disaggregated in a round-robin order instead of using a static hash. The
        stateless traffic includes non-IP L2 traffic, ICMP, some UDP protocols,
        and so on.
      - When creating a new VLAN, if this parameter is not specified, the default
        of (no) is used.
    type: bool
    version_added: 2.5
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
  source_check:
    description:
      - When C(yes), specifies that the system verifies that the return route to an initial
        packet is the same VLAN from which the packet originated.
      - The system performs this verification only if the C(auto_last_hop) option is C(no).
    type: bool
    version_added: 2.8
  fail_safe:
    description:
      - When C(yes), specifies that the VLAN takes the specified C(fail_safe_action) if the
        system detects a loss of traffic on this VLAN's interfaces.
    type: bool
    version_added: 2.8
  fail_safe_timeout:
    description:
      - Specifies the number of seconds that a system can run without detecting network
        traffic on this VLAN before it takes the C(fail_safe_action).
    type: int
    version_added: 2.8
  fail_safe_action:
    description:
      - Specifies the action that the system takes when it does not detect any traffic on
        this VLAN, and the C(fail_safe_timeout) has expired.
    type: str
    choices:
      - reboot
      - restart-all
      - failover
    version_added: 2.8
  sflow_poll_interval:
    description:
      - Specifies the maximum interval in seconds between two pollings.
    type: int
    version_added: 2.8
  sflow_sampling_rate:
    description:
      - Specifies the ratio of packets observed to the samples generated.
    type: int
    version_added: 2.8
  interfaces:
    description:
      - Interfaces that you want added to the VLAN. This can include both tagged
        and untagged interfaces as the C(tagging) parameter specifies.
      - This parameter is mutually exclusive with the C(untagged_interfaces) and
        C(tagged_interfaces) parameters.
    suboptions:
      interface:
        description:
          - The name of the interface
        type: str
      tagging:
        description:
          - Whether the interface is C(tagged) or C(untagged).
        type: str
        choices:
          - tagged
          - untagged
    type: list
    version_added: 2.8
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
    name: net1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set VLAN tag
  bigip_vlan:
    name: net1
    tag: 2345
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Add VLAN 2345 as tagged to interface 1.1
  bigip_vlan:
    tagged_interface: 1.1
    name: net1
    tag: 2345
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Add VLAN 1234 as tagged to interfaces 1.1 and 1.2
  bigip_vlan:
    tagged_interfaces:
      - 1.1
      - 1.2
    name: net1
    tag: 1234
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The description set on the VLAN.
  returned: changed
  type: str
  sample: foo VLAN
interfaces:
  description: Interfaces that the VLAN is assigned to.
  returned: changed
  type: list
  sample: ['1.1','1.2']
partition:
  description: The partition that the VLAN was created on.
  returned: changed
  type: str
  sample: Common
tag:
  description: The ID of the VLAN.
  returned: changed
  type: int
  sample: 2345
cmp_hash:
  description: New traffic disaggregation method.
  returned: changed
  type: str
  sample: source-address
dag_tunnel:
  description: The new DAG tunnel setting.
  returned: changed
  type: str
  sample: outer
source_check:
  description: The new Source Check setting.
  returned: changed
  type: bool
  sample: yes
fail_safe:
  description: The new Fail Safe setting.
  returned: changed
  type: bool
  sample: no
fail_safe_timeout:
  description: The new Fail Safe Timeout setting.
  returned: changed
  type: int
  sample: 90
fail_safe_action:
  description: The new Fail Safe Action setting.
  returned: changed
  type: str
  sample: reboot
sflow_poll_interval:
  description: The new sFlow Polling Interval setting.
  returned: changed
  type: int
  sample: 10
sflow_sampling_rate:
  description: The new sFlow Sampling Rate setting.
  returned: changed
  type: int
  sample: 20
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import compare_complex_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import compare_complex_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'cmpHash': 'cmp_hash',
        'dagTunnel': 'dag_tunnel',
        'dagRoundRobin': 'dag_round_robin',
        'interfacesReference': 'interfaces',
        'sourceChecking': 'source_check',
        'failsafe': 'fail_safe',
        'failsafeAction': 'fail_safe_action',
        'failsafeTimeout': 'fail_safe_timeout',
    }

    api_attributes = [
        'description',
        'interfaces',
        'tag',
        'mtu',
        'cmpHash',
        'dagTunnel',
        'dagRoundRobin',
        'sourceChecking',
        'failsafe',
        'failsafeAction',
        'failsafeTimeout',
        'sflow',
    ]

    updatables = [
        'interfaces',
        'tagged_interfaces',
        'untagged_interfaces',
        'tag',
        'description',
        'mtu',
        'cmp_hash',
        'dag_tunnel',
        'dag_round_robin',
        'source_check',
        'fail_safe',
        'fail_safe_action',
        'fail_safe_timeout',
        'sflow_poll_interval',
        'sflow_sampling_rate',
        'sflow',
    ]

    returnables = [
        'description',
        'partition',
        'tag',
        'interfaces',
        'tagged_interfaces',
        'untagged_interfaces',
        'mtu',
        'cmp_hash',
        'dag_tunnel',
        'dag_round_robin',
        'source_check',
        'fail_safe',
        'fail_safe_action',
        'fail_safe_timeout',
        'sflow_poll_interval',
        'sflow_sampling_rate',
        'sflow',
    ]

    @property
    def source_check(self):
        return flatten_boolean(self._values['source_check'])

    @property
    def fail_safe(self):
        return flatten_boolean(self._values['fail_safe'])


class ApiParameters(Parameters):
    @property
    def interfaces(self):
        if self._values['interfaces'] is None:
            return None
        if 'items' not in self._values['interfaces']:
            return None
        result = []
        for item in self._values['interfaces']['items']:
            name = item['name']
            if 'tagged' in item:
                tagged = item['tagged']
                result.append(dict(name=name, tagged=tagged))
            if 'untagged' in item:
                untagged = item['untagged']
                result.append(dict(name=name, untagged=untagged))
        return result

    @property
    def tagged_interfaces(self):
        if self.interfaces is None:
            return None
        result = [str(x['name']) for x in self.interfaces if 'tagged' in x and x['tagged'] is True]
        result = sorted(result)
        return result

    @property
    def untagged_interfaces(self):
        if self.interfaces is None:
            return None
        result = [str(x['name']) for x in self.interfaces if 'untagged' in x and x['untagged'] is True]
        result = sorted(result)
        return result

    @property
    def sflow_poll_interval(self):
        try:
            return self._values['sflow']['pollInterval']
        except (KeyError, TypeError):
            return None

    @property
    def sflow_sampling_rate(self):
        try:
            return self._values['sflow']['samplingRate']
        except (KeyError, TypeError):
            return None


class ModuleParameters(Parameters):
    @property
    def interfaces(self):
        if self._values['interfaces'] is None:
            return None
        elif len(self._values['interfaces']) == 1 and self._values['interfaces'][0] in ['', 'none']:
            return ''
        result = []
        for item in self._values['interfaces']:
            if 'interface' not in item:
                raise F5ModuleError(
                    "An 'interface' key must be provided when specifying a list of interfaces."
                )
            if 'tagging' not in item:
                raise F5ModuleError(
                    "A 'tagging' key must be provided when specifying a list of interfaces."
                )
            name = str(item['interface'])
            tagging = item['tagging']

            if tagging == 'tagged':
                result.append(dict(name=name, tagged=True))
            else:
                result.append(dict(name=name, untagged=True))
        return result

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
    @property
    def source_check(self):
        if self._values['source_check'] is None:
            return None
        if self._values['source_check'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def fail_safe(self):
        if self._values['fail_safe'] is None:
            return None
        if self._values['fail_safe'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def tagged_interfaces(self):
        if self.interfaces is None:
            return None
        result = [str(x['name']) for x in self.interfaces if 'tagged' in x and x['tagged'] is True]
        result = sorted(result)
        return result

    @property
    def untagged_interfaces(self):
        if self.interfaces is None:
            return None
        result = [str(x['name']) for x in self.interfaces if 'untagged' in x and x['untagged'] is True]
        result = sorted(result)
        return result

    @property
    def source_check(self):
        return flatten_boolean(self._values['source_check'])

    @property
    def fail_safe(self):
        return flatten_boolean(self._values['fail_safe'])

    @property
    def sflow(self):
        return None

    @property
    def sflow_poll_interval(self):
        try:
            return self._values['sflow']['pollInterval']
        except (KeyError, TypeError):
            return None

    @property
    def sflow_sampling_rate(self):
        try:
            return self._values['sflow']['samplingRate']
        except (KeyError, TypeError):
            return None


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
    def interfaces(self):
        if self.want.interfaces is None:
            return None
        if self.have.interfaces is None and self.want.interfaces in ['', 'none']:
            return None
        if self.have.interfaces is not None and self.want.interfaces in ['', 'none']:
            return []
        if self.have.interfaces is None:
            return dict(
                interfaces=self.want.interfaces
            )
        return compare_complex_list(self.want.interfaces, self.have.interfaces)

    @property
    def untagged_interfaces(self):
        result = self.cmp_interfaces(self.want.untagged_interfaces, self.have.untagged_interfaces, False)
        return result

    @property
    def tagged_interfaces(self):
        result = self.cmp_interfaces(self.want.tagged_interfaces, self.have.tagged_interfaces, True)
        return result

    def cmp_interfaces(self, want, have, tagged):
        result = []
        if tagged:
            tag_key = 'tagged'
        else:
            tag_key = 'untagged'
        if want is None:
            return None
        elif want == '' and have is None:
            return None
        elif want == '' and len(have) > 0:
            pass
        elif not have:
            result = dict(
                interfaces=[{'name': x, tag_key: True} for x in want]
            )
        elif set(want) != set(have):
            result = dict(
                interfaces=[{'name': x, tag_key: True} for x in want]
            )
        else:
            return None
        return result

    @property
    def sflow(self):
        result = {}
        s = self.sflow_poll_interval
        if s:
            result.update(s)
        s = self.sflow_sampling_rate
        if s:
            result.update(s)
        if result:
            return dict(
                sflow=result
            )

    @property
    def sflow_poll_interval(self):
        if self.want.sflow_poll_interval is None:
            return None
        if self.want.sflow_poll_interval != self.have.sflow_poll_interval:
            return dict(
                pollInterval=self.want.sflow_poll_interval
            )

    @property
    def sflow_sampling_rate(self):
        if self.want.sflow_sampling_rate is None:
            return None
        if self.want.sflow_sampling_rate != self.have.sflow_sampling_rate:
            return dict(
                samplingRate=self.want.sflow_sampling_rate
            )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
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
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/vlan".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}".format(
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/vlan/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        query = '?expandSubcollections=true'
        resp = self.client.api.get(uri + query)
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
            interfaces=dict(
                type='list',
                options=dict(
                    interface=dict(),
                    tagging=dict(
                        choice=['tagged', 'untagged']
                    )
                )
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
            source_check=dict(type='bool'),
            fail_safe=dict(type='bool'),
            fail_safe_timeout=dict(type='int'),
            fail_safe_action=dict(
                choices=['reboot', 'restart-all', 'failover']
            ),
            sflow_poll_interval=dict(type='int'),
            sflow_sampling_rate=dict(type='int'),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['tagged_interfaces', 'untagged_interfaces', 'interfaces'],
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )
    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
