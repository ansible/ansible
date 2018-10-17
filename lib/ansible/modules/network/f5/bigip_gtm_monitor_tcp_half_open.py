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
module: bigip_gtm_monitor_tcp_half_open
short_description: Manages F5 BIG-IP GTM tcp half-open monitors
description:
  - Manages F5 BIG-IP GTM tcp half-open monitors.
version_added: 2.6
options:
  name:
    description:
      - Monitor name.
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(tcp_half_open)
        parent on the C(Common) partition.
    default: "/Common/tcp_half_open"
  ip:
    description:
      - IP address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'.
  port:
    description:
      - Port address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'. Note that if specifying an IP address, a value between 1 and 65535
        must be specified
  interval:
    description:
      - Specifies, in seconds, the frequency at which the system issues the monitor
        check when either the resource is down or the status of the resource is unknown.
      - When creating a new monitor, if this parameter is not provided, then the
        default value will be C(30). This value B(must) be less than the C(timeout) value.
  timeout:
    description:
      - Specifies the number of seconds the target has in which to respond to the
        monitor request.
      - If the target responds within the set time period, it is considered up.
      - If the target does not respond within the set time period, it is considered down.
      - When this value is set to 0 (zero), the system uses the interval from the parent monitor.
      - When creating a new monitor, if this parameter is not provided, then
        the default value will be C(120).
  probe_interval:
    description:
      - Specifies the number of seconds the big3d process waits before sending out a
        subsequent probe attempt when a probe fails and multiple probe attempts have
        been requested.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(1).
  probe_timeout:
    description:
      - Specifies the number of seconds after which the system times out the probe request
        to the system.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(5).
  probe_attempts:
    description:
      - Specifies the number of times the system attempts to probe the host server, after
        which the system considers the host server down or unavailable.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(3).
  ignore_down_response:
    description:
      - Specifies that the monitor allows more than one probe attempt per interval.
      - When C(yes), specifies that the monitor ignores down responses for the duration of
        the monitor timeout. Once the monitor timeout is reached without the system receiving
        an up response, the system marks the object down.
      - When C(no), specifies that the monitor immediately marks an object down when it
        receives a down response.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(no).
    type: bool
  transparent:
    description:
      - Specifies whether the monitor operates in transparent mode.
      - A monitor in transparent mode directs traffic through the associated pool members
        or nodes (usually a router or firewall) to the aliased destination (that is, it
        probes the C(ip)-C(port) combination specified in the monitor).
      - If the monitor cannot successfully reach the aliased destination, the pool member
        or node through which the monitor traffic was sent is marked down.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(no).
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  state:
    description:
      - When C(present), ensures that the monitor exists.
      - When C(absent), ensures the monitor is removed.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires BIG-IP software version >= 12
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create TCP half-open Monitor
  bigip_gtm_monitor_tcp_half_open:
    state: present
    ip: 10.10.10.10
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_monitor
  delegate_to: localhost

- name: Remove TCP half-open Monitor
  bigip_gtm_monitor_tcp_half_open:
    state: absent
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_monitor
  delegate_to: localhost

- name: Add half-open monitor for all addresses, port 514
  bigip_gtm_monitor_tcp_half_open:
    server: lb.mydomain.com
    user: admin
    port: 514
    password: secret
    name: my_monitor
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: string
  sample: tcp_half_open
ip:
  description: The new IP of IP/port definition.
  returned: changed
  type: string
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
probe_timeout:
  description: The new timeout in which the system will timeout the monitor probe.
  returned: changed
  type: int
  sample: 10
probe_interval:
  description: The new interval in which the system will check the monitor probe.
  returned: changed
  type: int
  sample: 10
probe_attempts:
  description: The new number of attempts the system will make in checking the monitor probe.
  returned: changed
  type: int
  sample: 10
'''

import os

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

try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'ignoreDownResponse': 'ignore_down_response',
        'probeAttempts': 'probe_attempts',
        'probeInterval': 'probe_interval',
        'probeTimeout': 'probe_timeout'
    }

    api_attributes = [
        'defaultsFrom', 'interval', 'timeout', 'destination', 'transparent', 'probeAttempts',
        'probeInterval', 'probeTimeout', 'ignoreDownResponse'
    ]

    returnables = [
        'parent', 'ip', 'port', 'interval', 'timeout', 'transparent', 'probe_attempts',
        'probe_interval', 'probe_timeout', 'ignore_down_response'
    ]

    updatables = [
        'destination', 'interval', 'timeout', 'transparent', 'probe_attempts',
        'probe_interval', 'probe_timeout', 'ignore_down_response'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result

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
    def probe_attempts(self):
        if self._values['probe_attempts'] is None:
            return None
        return int(self._values['probe_attempts'])

    @property
    def probe_interval(self):
        if self._values['probe_interval'] is None:
            return None
        return int(self._values['probe_interval'])

    @property
    def probe_timeout(self):
        if self._values['probe_timeout'] is None:
            return None
        return int(self._values['probe_timeout'])

    @property
    def type(self):
        return 'tcp_half_open'


class ApiParameters(Parameters):
    @property
    def ip(self):
        ip, port = self._values['destination'].split(':')
        return ip

    @property
    def port(self):
        ip, port = self._values['destination'].split(':')
        return int(port)

    @property
    def ignore_down_response(self):
        if self._values['ignore_down_response'] is None:
            return None
        if self._values['ignore_down_response'] == 'disabled':
            return False
        return True

    @property
    def transparent(self):
        if self._values['transparent'] is None:
            return None
        if self._values['transparent'] == 'disabled':
            return False
        return True


class ModuleParameters(Parameters):
    @property
    def destination(self):
        if self.ip is None and self.port is None:
            return None
        destination = '{0}:{1}'.format(self.ip, self.port)
        return destination

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        if self._values['parent'].startswith('/'):
            parent = os.path.basename(self._values['parent'])
            result = '/{0}/{1}'.format(self.partition, parent)
        else:
            result = '/{0}/{1}'.format(self.partition, self._values['parent'])
        return result

    @property
    def ip(self):
        if self._values['ip'] is None:
            return None
        try:
            if self._values['ip'] in ['*', '0.0.0.0']:
                return '*'
            result = str(netaddr.IPAddress(self._values['ip']))
            return result
        except netaddr.core.AddrFormatError:
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


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def transparent(self):
        if self._values['transparent']:
            return 'enabled'
        return 'disabled'

    @property
    def ignore_down_response(self):
        if self._values['ignore_down_response']:
            return 'enabled'
        return 'disabled'


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

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
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
                changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        self._set_changed_options()
        if self.want.timeout is None:
            self.want.update({'timeout': 120})
        if self.want.interval is None:
            self.want.update({'interval': 30})
        if self.want.ip is None:
            self.want.update({'ip': '*'})
        if self.want.port is None:
            self.want.update({'port': '*'})
        if self.want.probe_interval is None:
            self.want.update({'probe_interval': 1})
        if self.want.probe_timeout is None:
            self.want.update({'probe_timeout': 5})
        if self.want.probe_attempts is None:
            self.want.update({'probe_attempts': 3})
        if self.want.ignore_down_response is None:
            self.want.update({'ignore_down_response': False})
        if self.want.transparent is None:
            self.want.update({'transparent': False})
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the monitor.")
        return True

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.monitor.tcp_half_opens.tcp_half_open.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def exists(self):
        result = self.client.api.tm.gtm.monitor.tcp_half_opens.tcp_half_open.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.changes.api_params()
        result = self.client.api.tm.gtm.monitor.tcp_half_opens.tcp_half_open.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.gtm.monitor.tcp_half_opens.tcp_half_open.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        result = self.client.api.tm.gtm.monitor.tcp_half_opens.tcp_half_open.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            parent=dict(default='/Common/tcp_half_open'),
            ip=dict(),
            port=dict(type='int'),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            probe_interval=dict(type='int'),
            probe_timeout=dict(type='int'),
            probe_attempts=dict(type='int'),
            ignore_down_response=dict(type='bool'),
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
        supports_check_mode=spec.supports_check_mode
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
