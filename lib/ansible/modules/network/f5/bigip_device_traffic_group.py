#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_device_traffic_group
short_description: Manages traffic groups on BIG-IP
description:
  - Supports managing traffic groups and their attributes on a BIG-IP.
version_added: 2.5
options:
  name:
    description:
      - The name of the traffic group.
    type: str
    required: True
  mac_address:
    description:
      - Specifies the floating Media Access Control (MAC) address associated with the floating IP addresses
        defined for a traffic group.
      - Primarily, a MAC masquerade address minimizes ARP communications or dropped packets as a result of failover.
      - A MAC masquerade address ensures that any traffic destined for a specific traffic group reaches an available
        device after failover, which happens because along with the traffic group, the MAC masquerade address floats
        to the available device.
      - Without a MAC masquerade address, the sending host must learn the MAC address for a newly-active device,
        either by sending an ARP request or by relying on the gratuitous ARP from the newly-active device.
      - To unset the MAC address, specify an empty value (C("")) to this parameter.
    type: str
    version_added: 2.6
  ha_order:
    description:
      - Specifies order in which you would like to assign devices for failover.
      - If you configure this setting, you must configure the setting on every traffic group in the device group.
      - The values should be device names of the devices that belong to the failover group configured beforehand.
      - The order in which the devices are placed as arguments to this parameter, determines their HA order
        on the device, in other words changing the order of the same elements will cause a change on the unit.
      - To disable an HA order failover method , specify an empty string value (C("")) to this parameter.
      - Disabling HA order will revert the device back to using Load Aware method as it is the default,
        unless C(ha_group) setting is also configured.
      - Device names will be prepended by a partition by the module, so you can provide either the full path format
        name C(/Common/bigip1) or just the name string C(bigip1).
    type: list
    version_added: 2.8
  ha_group:
    description:
      - Specifies a configured C(HA group) to be associated with the traffic group.
      - Once you create an HA group on a device and associate the HA group with a traffic group,
        you must create an HA group and associate it with that same traffic group on every device in the device group.
      - To disable an HA group failover method , specify an empty string value (C("")) to this parameter.
      - Disabling HA group will revert the device back to using C(Load Aware) method as it is the default,
        unless C(ha_order) setting is also configured.
      - The C(auto_failback) and C(auto_failback_time) are not compatible with C(ha_group).
    type: str
    version_added: 2.8
  ha_load_factor:
    description:
      - The value of the load the traffic-group presents the system relative to other traffic groups.
      - This parameter only takes effect when C(Load Aware) failover method is in use.
      - The correct value range is C(1 - 1000) inclusive.
    type: int
    version_added: 2.8
  auto_failback:
    description:
      - Specifies whether the traffic group fails back to the initial device specified in C(ha_order).
    type: bool
    version_added: 2.8
  auto_failback_time:
    description:
      - Specifies the number of seconds the system delays before failing back to the initial device
        specified in C(ha_order).
      - The correct value range is C(0 - 300) inclusive.
    type: int
    version_added: 2.8
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the traffic group exists.
      - When C(absent), ensures the traffic group is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a traffic group
  bigip_device_traffic_group:
    name: foo1
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Create a traffic group with ha_group failover
  bigip_device_traffic_group:
    name: foo2
    state: present
    ha_group: foo_HA_grp
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Create a traffic group with ha_order failover
  bigip_device_traffic_group:
    name: foo3
    state: present
    ha_order:
      - /Common/bigip1.lab.local
      - /Common/bigip2.lab.local
    auto_failback: yes
    auto_failback_time: 40
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Change traffic group ha_order to ha_group
  bigip_device_traffic_group:
    name: foo3
    state: present
    ha_group: foo_HA_grp
    ha_order: ""
    auto_failback: no
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Remove traffic group
  bigip_device_traffic_group:
    name: foo
    state: absent
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
mac_address:
  description: The MAC masquerade address
  returned: changed
  type: str
  sample: "02:01:d7:93:35:08"
ha_group:
  description: The configured HA group associated with traffic group
  returned: changed
  type: str
  sample: foo_HA_grp
ha_order:
  description: Specifies the order in which the devices will failover
  returned: changed
  type: list
  sample: ['/Common/bigip1', '/Common/bigip2']
ha_load_factor:
  description: The value of the load the traffic-group presents the system relative to other traffic groups
  returned: changed
  type: int
  sample: 20
auto_failback:
  description: Specifies whether the traffic group fails back to the initial device specified in ha_order
  returned: changed
  type: bool
  sample: yes
auto_failback_time:
  description: Specifies the number of seconds the system delays before failing back
  returned: changed
  type: int
  sample: 60
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean


class Parameters(AnsibleF5Parameters):
    api_map = {
        'mac': 'mac_address',
        'haGroup': 'ha_group',
        'haOrder': 'ha_order',
        'haLoadFactor': 'ha_load_factor',
        'autoFailbackTime': 'auto_failback_time',
        'autoFailbackEnabled': 'auto_failback',
    }

    api_attributes = [
        'mac',
        'haGroup',
        'haOrder',
        'haLoadFactor',
        'autoFailbackTime',
        'autoFailbackEnabled',

    ]

    returnables = [
        'mac_address',
        'ha_group',
        'ha_order',
        'ha_load_factor',
        'auto_failback_time',
        'auto_failback',
    ]

    updatables = [
        'mac_address',
        'ha_group',
        'ha_order',
        'ha_load_factor',
        'auto_failback_time',
        'auto_failback',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def mac_address(self):
        if self._values['mac_address'] is None:
            return None
        if self._values['mac_address'] == '':
            return 'none'
        return self._values['mac_address']

    @property
    def ha_group(self):
        if self._values['ha_group'] is None:
            return None
        if self._values['ha_group'] == '':
            return 'none'
        if self.auto_failback == 'true':
            raise F5ModuleError(
                "The auto_failback cannot be enabled when ha_group is specified."
            )
        return self._values['ha_group']

    @property
    def ha_load_factor(self):
        if self._values['ha_load_factor'] is None:
            return None
        value = self._values['ha_load_factor']
        if value < 1 or value > 1000:
            raise F5ModuleError(
                "Invalid ha_load_factor value, correct range is 1 - 1000, specified value: {0}.".format(value))
        return value

    @property
    def auto_failback_time(self):
        if self._values['auto_failback_time'] is None:
            return None
        value = self._values['auto_failback_time']
        if value < 0 or value > 300:
            raise F5ModuleError(
                "Invalid auto_failback_time value, correct range is 0 - 300, specified value: {0}.".format(value))
        return value

    @property
    def auto_failback(self):
        result = flatten_boolean(self._values['auto_failback'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return None

    @property
    def ha_order(self):
        if self._values['ha_order'] is None:
            return None
        if len(self._values['ha_order']) == 1 and self._values['ha_order'][0] == '':
            if self.auto_failback == 'true':
                raise F5ModuleError(
                    'Cannot enable auto failback when HA order list is empty, at least one device must be specified.'
                )
            return 'none'
        result = [fq_name(self.partition, value) for value in self._values['ha_order']]
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):

    @property
    def mac_address(self):
        if self._values['mac_address'] is None:
            return None
        if self._values['mac_address'] == 'none':
            return ''
        return self._values['mac_address']

    @property
    def ha_group(self):
        if self._values['ha_group'] is None:
            return None
        if self._values['ha_group'] == 'none':
            return ''
        return self._values['ha_group']

    @property
    def auto_failback(self):
        result = self._values['auto_failback']
        if result == 'true':
            return 'yes'
        if result == 'false':
            return 'no'
        return None

    @property
    def ha_order(self):
        if self._values['ha_order'] is None:
            return None
        if self._values['ha_order'] == 'none':
            return ''
        return self._values['ha_order']


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
    def ha_group(self):
        if self.want.ha_group is None:
            return None
        if self.have.ha_group is None and self.want.ha_group == 'none':
            return None
        if self.want.ha_group != self.have.ha_group:
            if self.have.auto_failback == 'true' and self.want.auto_failback != 'false':
                raise F5ModuleError(
                    "The auto_failback parameter on the device must disabled to use ha_group failover method."
                )
            return self.want.ha_group

    @property
    def ha_order(self):
        # Device order is literally derived from the order in the array,
        # hence lists with the same elements but in different order cannot be equal, so cmp_simple_list
        # function will not work here.
        if self.want.ha_order is None:
            return None
        if self.have.ha_order is None and self.want.ha_order == 'none':
            return None
        if self.want.ha_order != self.have.ha_order:
            return self.want.ha_order

    @property
    def partition(self):
        raise F5ModuleError(
            "Partition cannot be changed for a traffic group. Only /Common is allowed."
        )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
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
        if self.want.partition.lower().strip('/') != 'common':
            raise F5ModuleError(
                "Traffic groups can only be created in the /Common partition"
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/{2}".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/cm/traffic-group/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            mac_address=dict(),
            ha_order=dict(
                type='list'
            ),
            ha_group=dict(),
            ha_load_factor=dict(
                type='int'
            ),
            auto_failback=dict(
                type='bool',
            ),
            auto_failback_time=dict(
                type='int'
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),

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
