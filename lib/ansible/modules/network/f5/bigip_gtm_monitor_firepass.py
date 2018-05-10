#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_gtm_monitor_firepass
short_description: Manages F5 BIG-IP GTM FirePass monitors
description:
  - Manages F5 BIG-IP GTM FirePass monitors.
version_added: 2.6
options:
  name:
    description:
      - Monitor name.
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(tcp)
        parent on the C(Common) partition.
    default: /Common/firepass_gtm
  ip:
    description:
      - IP address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'.
      - If this value is an IP address, then a C(port) number must be specified.
  port:
    description:
      - Port address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'. Note that if specifying an IP address, a value between 1 and 65535
        must be specified.
  interval:
    description:
      - The interval specifying how frequently the monitor instance of this
        template will run.
      - If this parameter is not provided when creating a new monitor, then
        the default value will be 30.
      - This value B(must) be less than the C(timeout) value.
  timeout:
    description:
      - The number of seconds in which the node or service must respond to
        the monitor request. If the target responds within the set time
        period, it is considered up. If the target does not respond within
        the set time period, it is considered down. You can change this
        number to any number you want, however, it should be 3 times the
        interval number of seconds plus 1 second.
      - If this parameter is not provided when creating a new monitor, then
        the default value will be 90.
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
  probe_timeout:
    description:
      - Specifies the number of seconds after which the system times out the probe request
        to the system.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(5).
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
  target_username:
    description:
      - Specifies the user name, if the monitored target requires authentication.
  target_password:
    description:
      - Specifies the password, if the monitored target requires authentication.
  update_password:
    description:
      - C(always) will update passwords if the C(target_password) is specified.
      - C(on_create) will only set the password for newly created monitors.
    default: always
    choices:
      - always
      - on_create
  cipher_list:
    description:
      - Specifies the list of ciphers for this monitor.
      - The items in the cipher list are separated with the colon C(:) symbol.
      - When creating a new monitor, if this parameter is not specified, the default
        list is C(HIGH:!ADH).
  max_load_average:
    description:
      - Specifies the number that the monitor uses to mark the Secure Access Manager
        system up or down.
      - The system compares the Max Load Average setting against a one-minute average
        of the Secure Access Manager system load.
      - When the Secure Access Manager system-load average falls within the specified
        Max Load Average, the monitor marks the Secure Access Manager system up.
      - When the average exceeds the setting, the monitor marks the system down.
      - When creating a new monitor, if this parameter is not specified, the default
        is C(12).
  concurrency_limit:
    description:
      - Specifies the maximum percentage of licensed connections currently in use under
        which the monitor marks the Secure Access Manager system up.
      - As an example, a setting of 95 percent means that the monitor marks the Secure
        Access Manager system up until 95 percent of licensed connections are in use.
      - When the number of in-use licensed connections exceeds 95 percent, the monitor
        marks the Secure Access Manager system down.
      - When creating a new monitor, if this parameter is not specified, the default is C(95).
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a GTM FirePass monitor
  bigip_gtm_monitor_firepass:
    name: my_monitor
    ip: 1.1.1.1
    port: 80
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove FirePass Monitor
  bigip_gtm_monitor_firepass:
    name: my_monitor
    state: absent
    server: lb.mydomain.com
    user: admin
    password: secret
  delegate_to: localhost

- name: Add FirePass monitor for all addresses, port 514
  bigip_gtm_monitor_firepass:
    name: my_monitor
    server: lb.mydomain.com
    user: admin
    port: 514
    password: secret
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: string
  sample: firepass_gtm
ip:
  description: The new IP of IP/port definition.
  returned: changed
  type: string
  sample: 10.12.13.14
port:
  description: The new port the monitor checks the resource on.
  returned: changed
  type: string
  sample: 8080
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
ignore_down_response:
  description: Whether to ignore the down response or not.
  returned: changed
  type: bool
  sample: True
probe_timeout:
  description: The new timeout in which the system will timeout the monitor probe.
  returned: changed
  type: int
  sample: 10
cipher_list:
  description: The new value for the cipher list.
  returned: changed
  type: string
  sample: +3DES:+kEDH
max_load_average:
  description: The new value for the max load average.
  returned: changed
  type: int
  sample: 12
concurrency_limit:
  description: The new value for the concurrency limit.
  returned: changed
  type: int
  sample: 95
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

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
        'probeTimeout': 'probe_timeout',
        'username': 'target_username',
        'password': 'target_password',
        'cipherlist': 'cipher_list',
        'concurrencyLimit': 'concurrency_limit',
        'maxLoadAverage': 'max_load_average'
    }

    api_attributes = [
        'defaultsFrom',
        'interval',
        'timeout',
        'destination',
        'probeTimeout',
        'ignoreDownResponse',
        'username',
        'password',
        'cipherlist',
        'concurrencyLimit',
        'maxLoadAverage'
    ]

    returnables = [
        'parent',
        'ip',
        'port',
        'interval',
        'timeout',
        'probe_timeout',
        'ignore_down_response',
        'cipher_list',
        'max_load_average',
        'concurrency_limit',
    ]

    updatables = [
        'destination',
        'interval',
        'timeout',
        'probe_timeout',
        'ignore_down_response',
        'ip',
        'port',
        'target_username',
        'target_password',
        'cipher_list',
        'max_load_average',
        'concurrency_limit',
    ]


class ApiParameters(Parameters):
    @property
    def ip(self):
        ip, port = self._values['destination'].split(':')
        return ip

    @property
    def port(self):
        ip, port = self._values['destination'].split(':')
        try:
            return int(port)
        except ValueError:
            return port

    @property
    def ignore_down_response(self):
        if self._values['ignore_down_response'] is None:
            return None
        if self._values['ignore_down_response'] == 'disabled':
            return False
        return True


class ModuleParameters(Parameters):
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
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        elif self._values['port'] == '*':
            return '*'
        return int(self._values['port'])

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
    def probe_timeout(self):
        if self._values['probe_timeout'] is None:
            return None
        return int(self._values['probe_timeout'])

    @property
    def max_load_average(self):
        if self._values['max_load_average'] is None:
            return None
        return int(self._values['max_load_average'])

    @property
    def concurrency_limit(self):
        if self._values['concurrency_limit'] is None:
            return None
        return int(self._values['concurrency_limit'])


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
    def ignore_down_response(self):
        if self._values['ignore_down_response'] is None:
            return None
        elif self._values['ignore_down_response'] is True:
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
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
        if self._values['ignore_down_response'] == 'enabled':
            return True
        return False


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
    def target_password(self):
        if self.want.target_password != self.have.target_password:
            if self.want.update_password == 'always':
                result = self.want.target_password
                return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _set_default_creation_values(self):
        if self.want.timeout is None:
            self.want.update({'timeout': 90})
        if self.want.interval is None:
            self.want.update({'interval': 30})
        if self.want.probe_timeout is None:
            self.want.update({'probe_timeout': 5})
        if self.want.ip is None:
            self.want.update({'ip': '*'})
        if self.want.port is None:
            self.want.update({'port': '*'})
        if self.want.ignore_down_response is None:
            self.want.update({'ignore_down_response': False})
        if self.want.cipher_list is None:
            self.want.update({'cipher_list': 'HIGH:!ADH'})
        if self.want.max_load_average is None:
            self.want.update({'max_load_average': 12})
        if self.want.concurrency_limit is None:
            self.want.update({'concurrency_limit': 95})

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        result = self.client.api.tm.gtm.monitor.firepass_s.firepass.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

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
        self._set_default_creation_values()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.gtm.monitor.firepass_s.firepass.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.gtm.monitor.firepass_s.firepass.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.monitor.firepass_s.firepass.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.monitor.firepass_s.firepass.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            parent=dict(default='/Common/firepass_gtm'),
            ip=dict(),
            port=dict(type='int'),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            ignore_down_response=dict(type='bool'),
            probe_timeout=dict(type='int'),
            target_username=dict(),
            target_password=dict(no_log=True),
            cipher_list=dict(),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
            max_load_average=dict(type='int'),
            concurrency_limit=dict(type='int'),
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
