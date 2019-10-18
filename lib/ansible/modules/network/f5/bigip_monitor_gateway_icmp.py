#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_monitor_gateway_icmp
short_description: Manages F5 BIG-IP LTM gateway ICMP monitors
description:
  - Manages gateway ICMP monitors on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - Monitor name.
    type: str
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the
        C(gateway_icmp) parent on the C(Common) partition.
    type: str
    default: /Common/gateway_icmp
  description:
    description:
      - The description of the monitor.
    type: str
  ip:
    description:
      - IP address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'.
    type: str
  port:
    description:
      - Port address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'. Note that if specifying an IP address, a value between 1 and 65535
        must be specified.
    type: str
  interval:
    description:
      - Specifies, in seconds, the frequency at which the system issues the
        monitor check when either the resource is down or the status of the
        resource is unknown.
    type: int
  timeout:
    description:
      - Specifies the number of seconds the target has in which to respond to
        the monitor request.
      - If the target responds within the set time period, it is considered 'up'.
        If the target does not respond within the set time period, it is considered
        'down'. When this value is set to 0 (zero), the system uses the interval
        from the parent monitor.
      - Note that C(timeout) and C(time_until_up) combine to control when a
        resource is set to up.
    type: int
  time_until_up:
    description:
      - Specifies the number of seconds to wait after a resource first responds
        correctly to the monitor before setting the resource to 'up'.
      - During the interval, all responses from the resource must be correct.
      - When the interval expires, the resource is marked 'up'.
      - A value of 0, means that the resource is marked up immediately upon
        receipt of the first correct response.
    type: int
  up_interval:
    description:
      - Specifies the interval for the system to use to perform the health check
        when a resource is up.
      - When C(0), specifies that the system uses the interval specified in
        C(interval) to check the health of the resource.
      - When any other number, enables specification of a different interval to
        use when checking the health of a resource that is up.
    type: int
  manual_resume:
    description:
      - Specifies whether the system automatically changes the status of a resource
        to B(enabled) at the next successful monitor check.
      - If you set this option to C(yes), you must manually re-enable the resource
        before the system can use it for load balancing connections.
      - When C(yes), specifies that you must manually re-enable the resource after an
        unsuccessful monitor check.
      - When C(no), specifies that the system automatically changes the status of a
        resource to B(enabled) at the next successful monitor check.
    type: bool
  adaptive:
    description:
      - Specifies whether adaptive response time monitoring is enabled for this monitor.
      - When C(yes), the monitor determines the state of a service based on how divergent
        from the mean latency a monitor probe for that service is allowed to be.
        Also, values for the C(allowed_divergence), C(adaptive_limit), and
        and C(sampling_timespan) will be enforced.
      - When C(disabled), the monitor determines the state of a service based on the
        C(interval), C(up_interval), C(time_until_up), and C(timeout) monitor settings.
    type: bool
  allowed_divergence_type:
    description:
      - When specifying a new monitor, if C(adaptive) is C(yes), the default is
        C(relative)
      - When C(absolute), the number of milliseconds the latency of a monitor probe
        can exceed the mean latency of a monitor probe for the service being probed.
        In typical cases, if the monitor detects three probes in a row that miss the
        latency value you set, the pool member or node is marked down.
      - When C(relative), the percentage of deviation the latency of a monitor probe
        can exceed the mean latency of a monitor probe for the service being probed.
    type: str
    choices:
      - relative
      - absolute
  allowed_divergence_value:
    description:
      - When specifying a new monitor, if C(adaptive) is C(yes), and C(type) is
        C(relative), the default is C(25) percent.
    type: int
  adaptive_limit:
    description:
      - Specifies the absolute number of milliseconds that may not be exceeded by a monitor
        probe, regardless of C(allowed_divergence) setting, for a probe to be
        considered successful.
      - This value applies regardless of the value of the C(allowed_divergence) setting.
      - While this value can be configured when C(adaptive) is C(no), it will not take
        effect on the system until C(adaptive) is C(yes).
    type: int
  sampling_timespan:
    description:
      - Specifies the length, in seconds, of the probe history window that the system
        uses to calculate the mean latency and standard deviation of a monitor probe.
      - While this value can be configured when C(adaptive) is C(no), it will not take
        effect on the system until C(adaptive) is C(yes).
    type: int
  transparent:
    description:
      - Specifies whether the monitor operates in transparent mode.
      - A monitor in transparent mode directs traffic through the associated pool members
        or nodes (usually a router or firewall) to the aliased destination (that is, it
        probes the C(ip)-C(port) combination specified in the monitor).
      - If the monitor cannot successfully reach the aliased destination, the pool member
        or node through which the monitor traffic was sent is marked down.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be whatever is provided by the C(parent).
    type: bool
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
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a monitor
  bigip_monitor_gateway_icmp:
    name: gw1
    adaptive: no
    interval: 1
    time_until_up: 0
    timeout: 3
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: str
  sample: gateway-icmp
ip:
  description: The new IP of IP/port definition.
  returned: changed
  type: str
  sample: 10.12.13.14
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
adaptive:
  description: Whether adaptive is enabled or not.
  returned: changed
  type: bool
  sample: yes
allowed_divergence_type:
  description: Type of divergence used for adaptive response time monitoring.
  returned: changed
  type: str
  sample: absolute
allowed_divergence_value:
  description:
    - Value of the type of divergence used for adaptive response time monitoring.
    - May be C(percent) or C(ms) depending on whether C(relative) or C(absolute).
  returned: changed
  type: int
  sample: 25
description:
  description: The description of the monitor.
  returned: changed
  type: str
  sample: Important Monitor
adaptive_limit:
  description: Absolute number of milliseconds that may not be exceeded by a monitor probe.
  returned: changed
  type: int
  sample: 200
sampling_timespan:
  description: Absolute number of milliseconds that may not be exceeded by a monitor probe.
  returned: changed
  type: int
  sample: 200
up_interval:
  description: Interval for the system to use to perform the health check when a resource is up.
  returned: changed
  type: int
  sample: 0
port:
  description:
    - Alias port or service for the monitor to check, on behalf of the pools or pool
      members with which the monitor is associated.
  returned: changed
  type: str
  sample: 80
transparent:
  description: Whether the monitor operates in transparent mode.
  returned: changed
  type: bool
  sample: no
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
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'adaptiveDivergenceType': 'allowed_divergence_type',
        'adaptiveDivergenceValue': 'allowed_divergence_value',
        'adaptiveLimit': 'adaptive_limit',
        'adaptiveSamplingTimespan': 'sampling_timespan',
        'timeUntilUp': 'time_until_up',
        'upInterval': 'up_interval',
        'defaultsFrom': 'parent',
    }

    api_attributes = [
        'adaptive',
        'adaptiveDivergenceType',
        'adaptiveDivergenceValue',
        'adaptiveLimit',
        'adaptiveSamplingTimespan',
        'defaultsFrom',
        'description',
        'destination',
        'interval',
        'manualResume',
        'timeout',
        'timeUntilUp',
        'transparent',
        'upInterval',
        'destination',
    ]

    returnables = [
        'adaptive',
        'allowed_divergence_type',
        'allowed_divergence_value',
        'description',
        'adaptive_limit',
        'sampling_timespan',
        'manual_resume',
        'time_until_up',
        'up_interval',
        'timeout',
        'interval',
        'transparent',
        'parent',
        'ip',
        'port',
    ]

    updatables = [
        'adaptive',
        'allowed_divergence_type',
        'allowed_divergence_value',
        'adaptive_limit',
        'sampling_timespan',
        'description',
        'manual_resume',
        'time_until_up',
        'up_interval',
        'timeout',
        'interval',
        'transparent',
        'parent',
        'destination',
        'interval',
    ]

    @property
    def destination(self):
        if self.ip is None and self.port is None:
            return None
        destination = '{0}:{1}'.format(self.ip, self.port)
        return destination

    @destination.setter
    def destination(self, value):
        ip, port = value.split(':')
        self._values['ip'] = ip
        self._values['port'] = port

    @property
    def interval(self):
        if self._values['interval'] is None:
            return None

        # Per BZ617284, the BIG-IP UI does not raise a warning about this.
        # So I do
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
    def ip(self):
        if self._values['ip'] is None:
            return None
        if self._values['ip'] in ['*', '0.0.0.0']:
            return '*'
        elif is_valid_ip(self._values['ip']):
            return self._values['ip']
        else:
            raise F5ModuleError(
                "The provided 'ip' parameter is not an IP address."
            )

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        elif self._values['port'] == '*':
            return '*'
        return int(self._values['port'])

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

    @property
    def manual_resume(self):
        if self._values['manual_resume'] is None:
            return None
        elif self._values['manual_resume'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def transparent(self):
        if self._values['transparent'] is None:
            return None
        elif self._values['transparent'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def adaptive(self):
        if self._values['adaptive'] is None:
            return None
        elif self._values['adaptive'] is True:
            return 'enabled'
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
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def transparent(self):
        return flatten_boolean(self._values['transparent'])

    @property
    def adaptive(self):
        return flatten_boolean(self._values['adaptive'])


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
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent monitor cannot be changed"
            )

    @property
    def destination(self):
        if self.want.ip is None and self.want.port is None:
            return None
        if self.want.port is None:
            self.want.update({'port': self.have.port})
        if self.want.ip is None:
            self.want.update({'ip': self.have.ip})

        if self.want.port in [None, '*'] and self.want.ip != '*':
            raise F5ModuleError(
                "Specifying an IP address requires that a port number be specified"
            )

        if self.want.destination != self.have.destination:
            return self.want.destination

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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp/{2}".format(
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

        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/gateway-icmp/{2}".format(
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
            parent=dict(default='/Common/gateway_icmp'),
            ip=dict(),
            description=dict(),
            port=dict(),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            time_until_up=dict(type='int'),
            up_interval=dict(type='int'),
            manual_resume=dict(type='bool'),
            adaptive=dict(type='bool'),
            allowed_divergence_type=dict(choices=['relative', 'absolute']),
            allowed_divergence_value=dict(type='int'),
            adaptive_limit=dict(type='int'),
            sampling_timespan=dict(type='int'),
            transparent=dict(type='bool'),
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
