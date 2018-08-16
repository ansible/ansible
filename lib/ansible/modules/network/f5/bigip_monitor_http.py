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
module: bigip_monitor_http
short_description: Manages F5 BIG-IP LTM http monitors
description: Manages F5 BIG-IP LTM http monitors.
version_added: 2.5
options:
  name:
    description:
      - Monitor name.
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(http)
        parent on the C(Common) partition.
    default: "/Common/http"
  send:
    description:
      - The send string for the monitor call. When creating a new monitor, if
        this value is not provided, the default C(GET /\r\n) will be used.
  receive:
    description:
      - The receive string for the monitor call.
  receive_disable:
    description:
      - This setting works like C(receive), except that the system marks the node
        or pool member disabled when its response matches the C(receive_disable)
        string but not C(receive). To use this setting, you must specify both
        C(receive_disable) and C(receive).
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
        must be specified.
  interval:
    description:
      - The interval specifying how frequently the monitor instance of this
        template will run. If this parameter is not provided when creating
        a new monitor, then the default value will be 5. This value B(must)
        be less than the C(timeout) value.
  timeout:
    description:
      - The number of seconds in which the node or service must respond to
        the monitor request. If the target responds within the set time
        period, it is considered up. If the target does not respond within
        the set time period, it is considered down. You can change this
        number to any number you want, however, it should be 3 times the
        interval number of seconds plus 1 second. If this parameter is not
        provided when creating a new monitor, then the default value will be 16.
  time_until_up:
    description:
      - Specifies the amount of time in seconds after the first successful
        response before a node will be marked up. A value of 0 will cause a
        node to be marked up immediately after a valid response is received
        from the node. If this parameter is not provided when creating
        a new monitor, then the default value will be 0.
  target_username:
    description:
      - Specifies the user name, if the monitored target requires authentication.
  target_password:
    description:
      - Specifies the password, if the monitored target requires authentication.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  state:
    description:
      - When C(present), ensures that the monitor exists.
      - When C(absent), ensures the monitor is removed.
    default: present
    choices:
      - present
      - absent
    version_added: 2.5
notes:
  - Requires BIG-IP software version >= 12
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create HTTP Monitor
  bigip_monitor_http:
    state: present
    ip: 10.10.10.10
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_http_monitor
  delegate_to: localhost

- name: Remove HTTP Monitor
  bigip_monitor_http:
    state: absent
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_http_monitor
  delegate_to: localhost

- name: Include a username and password in the HTTP monitor
  bigip_monitor_http:
    state: absent
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_http_monitor
    target_username: monitor_user
    target_password: monitor_pass
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: string
  sample: http
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
time_until_up:
  description: The new time in which to mark a system as up after first successful response.
  returned: changed
  type: int
  sample: 2
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
        'timeUntilUp': 'time_until_up',
        'defaultsFrom': 'parent',
        'recv': 'receive',
        'recvDisable': 'receive_disable'
    }

    api_attributes = [
        'timeUntilUp', 'defaultsFrom', 'interval', 'timeout', 'recv', 'send',
        'destination', 'username', 'password', 'recvDisable'
    ]

    returnables = [
        'parent', 'send', 'receive', 'ip', 'port', 'interval', 'timeout',
        'time_until_up', 'receive_disable'
    ]

    updatables = [
        'destination', 'send', 'receive', 'interval', 'timeout', 'time_until_up',
        'target_username', 'target_password', 'receive_disable'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

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
    def type(self):
        return 'http'

    @property
    def username(self):
        return self._values['target_username']

    @property
    def password(self):
        return self._values['target_password']


class Changes(Parameters):
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
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

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
            self.changes = Changes(params=changed)
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
            self.want.update({'timeout': 16})
        if self.want.interval is None:
            self.want.update({'interval': 5})
        if self.want.time_until_up is None:
            self.want.update({'time_until_up': 0})
        if self.want.ip is None:
            self.want.update({'ip': '*'})
        if self.want.port is None:
            self.want.update({'port': '*'})
        if self.want.send is None:
            self.want.update({'send': 'GET /\r\n'})
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
        resource = self.client.api.tm.ltm.monitor.https.http.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(params=result)

    def exists(self):
        result = self.client.api.tm.ltm.monitor.https.http.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.ltm.monitor.https.http.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.ltm.monitor.https.http.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        result = self.client.api.tm.ltm.monitor.https.http.load(
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
            parent=dict(default='/Common/http'),
            send=dict(),
            receive=dict(),
            receive_disable=dict(required=False),
            ip=dict(),
            port=dict(type='int'),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            time_until_up=dict(type='int'),
            target_username=dict(),
            target_password=dict(no_log=True),
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
