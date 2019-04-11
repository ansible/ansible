#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_monitor_snmp_dca
short_description: Manages BIG-IP SNMP data collecting agent (DCA) monitors
description:
  - The BIG-IP has an SNMP data collecting agent (DCA) that can query remote
    SNMP agents of various types, including the UC Davis agent (UCD) and the
    Windows 2000 Server agent (WIN2000).
version_added: 2.5
options:
  name:
    description:
      - Monitor name.
    type: str
    required: True
  description:
    description:
      - Specifies descriptive text that identifies the monitor.
    type: str
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(snmp_dca)
        parent on the C(Common) partition.
    type: str
    default: "/Common/snmp_dca"
  interval:
    description:
      - Specifies, in seconds, the frequency at which the system issues the
        monitor check when either the resource is down or the status of the
        resource is unknown. When creating a new monitor, the default is C(10).
    type: int
  timeout:
    description:
      - Specifies the number of seconds the target has in which to respond to
        the monitor request. When creating a new monitor, the default is C(30)
        seconds. If the target responds within the set time period, it is
        considered 'up'. If the target does not respond within the set time
        period, it is considered 'down'. When this value is set to 0 (zero),
        the system uses the interval from the parent monitor. Note that
        C(timeout) and C(time_until_up) combine to control when a resource is
        set to up.
    type: int
  time_until_up:
    description:
      - Specifies the number of seconds to wait after a resource first responds
        correctly to the monitor before setting the resource to 'up'. During the
        interval, all responses from the resource must be correct. When the
        interval expires, the resource is marked 'up'. A value of 0, means
        that the resource is marked up immediately upon receipt of the first
        correct response. When creating a new monitor, the default is C(0).
    type: int
  community:
    description:
      - Specifies the community name that the system must use to authenticate
        with the host server through SNMP. When creating a new monitor, the
        default value is C(public). Note that this value is case sensitive.
    type: str
  version:
    description:
      - Specifies the version of SNMP that the host server uses. When creating
        a new monitor, the default is C(v1). When C(v1), specifies that the
        host server uses SNMP version 1. When C(v2c), specifies that the host
        server uses SNMP version 2c.
    type: str
    choices:
      - v1
      - v2c
  agent_type:
    description:
      - Specifies the SNMP agent running on the monitored server. When creating
        a new monitor, the default is C(UCD) (UC-Davis).
    type: str
    choices:
      - UCD
      - WIN2000
      - GENERIC
  cpu_coefficient:
    description:
      - Specifies the coefficient that the system uses to calculate the weight
        of the CPU threshold in the dynamic ratio load balancing algorithm.
        When creating a new monitor, the default is C(1.5).
    type: str
  cpu_threshold:
    description:
      - Specifies the maximum acceptable CPU usage on the target server. When
        creating a new monitor, the default is C(80) percent.
    type: int
  memory_coefficient:
    description:
      - Specifies the coefficient that the system uses to calculate the weight
        of the memory threshold in the dynamic ratio load balancing algorithm.
        When creating a new monitor, the default is C(1.0).
    type: str
  memory_threshold:
    description:
      - Specifies the maximum acceptable memory usage on the target server.
        When creating a new monitor, the default is C(70) percent.
    type: int
  disk_coefficient:
    description:
      - Specifies the coefficient that the system uses to calculate the weight
        of the disk threshold in the dynamic ratio load balancing algorithm.
        When creating a new monitor, the default is C(2.0).
    type: str
  disk_threshold:
    description:
      - Specifies the maximum acceptable disk usage on the target server. When
        creating a new monitor, the default is C(90) percent.
    type: int
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the monitor exists.
      - When C(absent), ensures the monitor is removed.
    type: str
    choices:
      - present
      - absent
    default: present
    version_added: 2.5
notes:
  - Requires BIG-IP software version >= 12
  - This module does not support the C(variables) option because this option
    is broken in the REST API and does not function correctly in C(tmsh); for
    example you cannot remove user-defined params. Therefore, there is no way
    to automatically configure it.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create SNMP DCS monitor
  bigip_monitor_snmp_dca:
    name: my_monitor
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove TCP Echo Monitor
  bigip_monitor_snmp_dca:
    name: my_monitor
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: str
  sample: snmp_dca
description:
  description: The description of the monitor.
  returned: changed
  type: str
  sample: Important Monitor
interval:
  description: The new interval in which to run the monitor check.
  returned: changed
  type: int
  sample: 2
timeout:
  description: The new timeout in which the remote system must respond to the monitor.
  returned: changed
  type: int
  sample: 10
time_until_up:
  description: The new time in which to mark a system as up after first successful response.
  returned: changed
  type: int
  sample: 2
community:
  description: The new community for the monitor.
  returned: changed
  type: str
  sample: foobar
version:
  description: The new new SNMP version to be used by the monitor.
  returned: changed
  type: str
  sample: v2c
agent_type:
  description: The new agent type to be used by the monitor.
  returned: changed
  type: str
  sample: UCD
cpu_coefficient:
  description: The new CPU coefficient.
  returned: changed
  type: float
  sample: 2.4
cpu_threshold:
  description: The new CPU threshold.
  returned: changed
  type: int
  sample: 85
memory_coefficient:
  description: The new memory coefficient.
  returned: changed
  type: float
  sample: 6.4
memory_threshold:
  description: The new memory threshold.
  returned: changed
  type: int
  sample: 50
disk_coefficient:
  description: The new disk coefficient.
  returned: changed
  type: float
  sample: 10.2
disk_threshold:
  description: The new disk threshold.
  returned: changed
  type: int
  sample: 34
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
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'timeUntilUp': 'time_until_up',
        'defaultsFrom': 'parent',
        'agentType': 'agent_type',
        'cpuCoefficient': 'cpu_coefficient',
        'cpuThreshold': 'cpu_threshold',
        'memoryCoefficient': 'memory_coefficient',
        'memoryThreshold': 'memory_threshold',
        'diskCoefficient': 'disk_coefficient',
        'diskThreshold': 'disk_threshold',
    }

    api_attributes = [
        'timeUntilUp',
        'defaultsFrom',
        'interval',
        'timeout',
        'destination',
        'community',
        'version',
        'agentType',
        'cpuCoefficient',
        'cpuThreshold',
        'memoryCoefficient',
        'memoryThreshold',
        'diskCoefficient',
        'diskThreshold',
        'description',
    ]

    returnables = [
        'parent',
        'ip',
        'interval',
        'timeout',
        'time_until_up',
        'description',
        'community',
        'version',
        'agent_type',
        'cpu_coefficient',
        'cpu_threshold',
        'memory_coefficient',
        'memory_threshold',
        'disk_coefficient',
        'disk_threshold',
    ]

    updatables = [
        'ip',
        'interval',
        'timeout',
        'time_until_up',
        'description',
        'community',
        'version',
        'agent_type',
        'cpu_coefficient',
        'cpu_threshold',
        'memory_coefficient',
        'memory_threshold',
        'disk_coefficient',
        'disk_threshold',
    ]

    @property
    def interval(self):
        if self._values['interval'] is None:
            return None
        if 1 > int(self._values['interval']) > 86400:
            raise F5ModuleError(
                "Interval value must be between 1 and 86400"
            )
        return int(self._values['interval'])

    @property
    def timeout(self):
        if self._values['timeout'] is None:
            return None
        return int(self._values['timeout'])

    @property
    def time_until_up(self):
        if self._values['time_until_up'] is None:
            return None
        return int(self._values['time_until_up'])

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def cpu_coefficient(self):
        result = self._get_numeric_property('cpu_coefficient')
        return result

    @property
    def cpu_threshold(self):
        result = self._get_numeric_property('cpu_threshold')
        return result

    @property
    def memory_coefficient(self):
        result = self._get_numeric_property('memory_coefficient')
        return result

    @property
    def memory_threshold(self):
        result = self._get_numeric_property('memory_threshold')
        return result

    @property
    def disk_coefficient(self):
        result = self._get_numeric_property('disk_coefficient')
        return result

    @property
    def disk_threshold(self):
        result = self._get_numeric_property('disk_threshold')
        return result

    def _get_numeric_property(self, property):
        if self._values[property] is None:
            return None
        try:
            fvar = float(self._values[property])
        except ValueError:
            raise F5ModuleError(
                "Provided {0} must be a valid number".format(property)
            )
        return fvar

    @property
    def type(self):
        return 'snmp_dca'


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']


class ModuleParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']


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
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            result = self.__default(param)
            return result

    @property
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent monitor cannot be changed"
            )

    @property
    def interval(self):
        if self.want.timeout is not None and self.want.interval is not None:
            if self.want.interval >= self.want.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        elif self.want.timeout is not None:
            if self.have.interval >= self.want.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        elif self.want.interval is not None:
            if self.want.interval >= self.have.timeout:
                raise F5ModuleError(
                    "Parameter 'interval' must be less than 'timeout'."
                )
        if self.want.interval != self.have.interval:
            return self.want.interval

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

    def should_update(self):
        result = self._update_changed_options()
        if result:
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
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/snmp-dca/{2}".format(
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
        self._set_default_creation_values()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def _set_default_creation_values(self):
        if self.want.timeout is None:
            self.want.update({'timeout': 30})
        if self.want.interval is None:
            self.want.update({'interval': 10})
        if self.want.time_until_up is None:
            self.want.update({'time_until_up': 0})
        if self.want.community is None:
            self.want.update({'community': 'public'})
        if self.want.version is None:
            self.want.update({'version': 'v1'})
        if self.want.agent_type is None:
            self.want.update({'agent_type': 'UCD'})
        if self.want.cpu_coefficient is None:
            self.want.update({'cpu_coefficient': '1.5'})
        if self.want.cpu_threshold is None:
            self.want.update({'cpu_threshold': '80'})
        if self.want.memory_coefficient is None:
            self.want.update({'memory_coefficient': '1.0'})
        if self.want.memory_threshold is None:
            self.want.update({'memory_threshold': '70'})
        if self.want.disk_coefficient is None:
            self.want.update({'disk_coefficient': '2.0'})
        if self.want.disk_threshold is None:
            self.want.update({'disk_threshold': '90'})

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/snmp-dca/".format(
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/snmp-dca/{2}".format(
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/snmp-dca/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/snmp-dca/{2}".format(
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
            description=dict(),
            parent=dict(default='/Common/snmp_dca'),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            time_until_up=dict(type='int'),
            community=dict(),
            version=dict(choices=['v1', 'v2c']),
            agent_type=dict(
                choices=['UCD', 'WIN2000', 'GENERIC']
            ),
            cpu_coefficient=dict(),
            cpu_threshold=dict(type='int'),
            memory_coefficient=dict(),
            memory_threshold=dict(type='int'),
            disk_coefficient=dict(),
            disk_threshold=dict(type='int'),
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
