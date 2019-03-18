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
module: bigip_gtm_monitor_http
short_description: Manages F5 BIG-IP GTM http monitors
description:
  - Manages F5 BIG-IP GTM http monitors.
version_added: 2.6
options:
  name:
    description:
      - Monitor name.
    type: str
    required: True
  parent:
    description:
      - The parent template of this monitor template. Once this value has
        been set, it cannot be changed. By default, this value is the C(tcp)
        parent on the C(Common) partition.
    type: str
    default: /Common/http
  send:
    description:
      - The send string for the monitor call.
      - When creating a new monitor, if this parameter is not provided, the
        default of C(GET /\r\n) will be used.
    type: str
  receive:
    description:
      - The receive string for the monitor call.
    type: str
  ip:
    description:
      - IP address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'.
      - If this value is an IP address, then a C(port) number must be specified.
    type: str
  port:
    description:
      - Port address part of the IP/port definition. If this parameter is not
        provided when creating a new monitor, then the default value will be
        '*'. Note that if specifying an IP address, a value between 1 and 65535
        must be specified
    type: str
  interval:
    description:
      - The interval specifying how frequently the monitor instance of this
        template will run.
      - If this parameter is not provided when creating a new monitor, then the
        default value will be 30.
      - This value B(must) be less than the C(timeout) value.
    type: int
  timeout:
    description:
      - The number of seconds in which the node or service must respond to
        the monitor request. If the target responds within the set time
        period, it is considered up. If the target does not respond within
        the set time period, it is considered down. You can change this
        number to any number you want, however, it should be 3 times the
        interval number of seconds plus 1 second.
      - If this parameter is not provided when creating a new monitor, then the
        default value will be 120.
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
  probe_timeout:
    description:
      - Specifies the number of seconds after which the system times out the probe request
        to the system.
      - When creating a new monitor, if this parameter is not provided, then the default
        value will be C(5).
    type: int
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
  reverse:
    description:
      - Instructs the system to mark the target resource down when the test is successful.
        This setting is useful, for example, if the content on your web site home page is
        dynamic and changes frequently, you may want to set up a reverse ECV service check
        that looks for the string Error.
      - A match for this string means that the web server was down.
      - To use this option, you must specify values for C(send) and C(receive).
    type: bool
  target_username:
    description:
      - Specifies the user name, if the monitored target requires authentication.
    type: str
  target_password:
    description:
      - Specifies the password, if the monitored target requires authentication.
    type: str
  update_password:
    description:
      - C(always) will update passwords if the C(target_password) is specified.
      - C(on_create) will only set the password for newly created monitors.
    type: str
    choices:
      - always
      - on_create
    default: always
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a GTM HTTP monitor
  bigip_gtm_monitor_http:
    name: my_monitor
    ip: 1.1.1.1
    port: 80
    send: my send string
    receive: my receive string
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Remove HTTP Monitor
  bigip_gtm_monitor_http:
    name: my_monitor
    state: absent
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Add HTTP monitor for all addresses, port 514
  bigip_gtm_monitor_http:
    name: my_monitor
    port: 514
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
parent:
  description: New parent template of the monitor.
  returned: changed
  type: str
  sample: http
ip:
  description: The new IP of IP/port definition.
  returned: changed
  type: str
  sample: 10.12.13.14
port:
  description: The new port the monitor checks the resource on.
  returned: changed
  type: str
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
send:
  description: The new send string for this monitor.
  returned: changed
  type: str
  sample: tcp string to send
receive:
  description: The new receive string for this monitor.
  returned: changed
  type: str
  sample: tcp string to receive
probe_timeout:
  description: The new timeout in which the system will timeout the monitor probe.
  returned: changed
  type: int
  sample: 10
reverse:
  description: The new value for whether the monitor operates in reverse mode.
  returned: changed
  type: bool
  sample: False
transparent:
  description: The new value for whether the monitor operates in transparent mode.
  returned: changed
  type: bool
  sample: False
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
    from library.module_utils.network.f5.icontrol import module_provisioned
    from library.module_utils.network.f5.ipaddress import is_valid_ip
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import module_provisioned
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultsFrom': 'parent',
        'ignoreDownResponse': 'ignore_down_response',
        'probeTimeout': 'probe_timeout',
        'recv': 'receive',
        'username': 'target_username',
        'password': 'target_password',
    }

    api_attributes = [
        'defaultsFrom',
        'interval',
        'timeout',
        'destination',
        'transparent',
        'probeTimeout',
        'ignoreDownResponse',
        'reverse',
        'send',
        'recv',
        'username',
        'password',
    ]

    returnables = [
        'parent',
        'ip',
        'port',
        'interval',
        'timeout',
        'transparent',
        'probe_timeout',
        'ignore_down_response',
        'send',
        'receive',
        'reverse',
    ]

    updatables = [
        'destination',
        'interval',
        'timeout',
        'transparent',
        'probe_timeout',
        'ignore_down_response',
        'send',
        'receive',
        'reverse',
        'ip',
        'port',
        'target_username',
        'target_password',
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

    @property
    def transparent(self):
        if self._values['transparent'] is None:
            return None
        if self._values['transparent'] == 'disabled':
            return False
        return True

    @property
    def reverse(self):
        if self._values['reverse'] is None:
            return None
        if self._values['reverse'] == 'disabled':
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
    def ip(self):  # lgtm [py/similar-function]
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
    def type(self):
        return 'http'


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
    def transparent(self):
        if self._values['transparent'] is None:
            return None
        elif self._values['transparent'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def ignore_down_response(self):
        if self._values['ignore_down_response'] is None:
            return None
        elif self._values['ignore_down_response'] is True:
            return 'enabled'
        return 'disabled'

    @property
    def reverse(self):
        if self._values['reverse'] is None:
            return None
        elif self._values['reverse'] is True:
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
    def transparent(self):
        if self._values['transparent'] == 'enabled':
            return True
        return False

    @property
    def ignore_down_response(self):
        if self._values['ignore_down_response'] == 'enabled':
            return True
        return False

    @property
    def reverse(self):
        if self._values['reverse'] == 'enabled':
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

    def _set_default_creation_values(self):
        if self.want.timeout is None:
            self.want.update({'timeout': 120})
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
        if self.want.transparent is None:
            self.want.update({'transparent': False})
        if self.want.send is None:
            self.want.update({'send': 'GET /\r\n'})

    def exec_module(self):
        if not module_provisioned(self.client, 'gtm'):
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
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

    def create(self):
        self._set_default_creation_values()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/monitor/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/monitor/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/gtm/monitor/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/gtm/monitor/http/".format(
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/monitor/http/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
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
            parent=dict(default='/Common/http'),
            send=dict(),
            receive=dict(),
            ip=dict(),
            port=dict(),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            ignore_down_response=dict(type='bool'),
            transparent=dict(type='bool'),
            probe_timeout=dict(type='int'),
            reverse=dict(type='bool'),
            target_username=dict(),
            target_password=dict(no_log=True),
            update_password=dict(
                default='always',
                choices=['always', 'on_create']
            ),
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
