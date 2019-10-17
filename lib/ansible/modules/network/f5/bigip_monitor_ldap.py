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
module: bigip_monitor_ldap
short_description: Manages BIG-IP LDAP monitors
description:
  - Manages BIG-IP LDAP monitors.
version_added: 2.8
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
        been set, it cannot be changed.
      - By default, this value is the C(ldap) parent on the C(Common) partition.
    type: str
    default: "/Common/ldap"
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
        '*'.
      - Note that if specifying an IP address, a value between 1 and 65535
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
  target_username:
    description:
      - Specifies the user name, if the monitored target requires authentication.
    type: str
  target_password:
    description:
      - Specifies the password, if the monitored target requires authentication.
    type: str
  base:
    description:
      - Specifies the location in the LDAP tree from which the monitor starts the
        health check.
    type: str
  filter:
    description:
      - Specifies an LDAP key for which the monitor searches.
    type: str
  security:
    description:
      - Specifies the secure protocol type for communications with the target.
    type: str
    choices:
      - none
      - ssl
      - tls
  mandatory_attributes:
    description:
      - Specifies whether the target must include attributes in its response to be
        considered up.
    type: bool
  chase_referrals:
    description:
      - Specifies whether, upon receipt of an LDAP referral entry, the target
        follows (or chases) that referral.
    type: bool
  debug:
    description:
      - Specifies whether the monitor sends error messages and additional information
        to a log file created and labeled specifically for this monitor.
    type: bool
  update_password:
    description:
      - C(always) will update passwords if the C(target_password) is specified.
      - C(on_create) will only set the password for newly created monitors.
    type: str
    choices:
      - always
      - on_create
    default: always
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
  - Greg Crosby (@crosbygw)
'''

EXAMPLES = r'''
- name: Create a LDAP monitor
  bigip_monitor_ldap:
    name: foo
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
  sample: ldap
description:
  description: The description of the monitor.
  returned: changed
  type: str
  sample: Important_Monitor
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
security:
  description: The new Security setting of the resource.
  returned: changed
  type: str
  sample: ssl
debug:
  description: The new Debug setting of the resource.
  returned: changed
  type: bool
  sample: yes
mandatory_attributes:
  description: The new Mandatory Attributes setting of the resource.
  returned: changed
  type: bool
  sample: no
chase_referrals:
  description: The new Chase Referrals setting of the resource.
  returned: changed
  type: bool
  sample: yes
manual_resume:
  description: The new Manual Resume setting of the resource.
  returned: changed
  type: bool
  sample: no
filter:
  description: The new LDAP Filter setting of the resource.
  returned: changed
  type: str
  sample: filter1
base:
  description: The new LDAP Base setting of the resource.
  returned: changed
  type: str
  sample: base
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
        'timeUntilUp': 'time_until_up',
        'defaultsFrom': 'parent',
        'mandatoryAttributes': 'mandatory_attributes',
        'chaseReferrals': 'chase_referrals',
        'manualResume': 'manual_resume',
        'username': 'target_username',
        'password': 'target_password',
    }

    api_attributes = [
        'timeUntilUp',
        'defaultsFrom',
        'interval',
        'timeout',
        'destination',
        'description',
        'security',
        'mandatoryAttributes',
        'chaseReferrals',
        'debug',
        'manualResume',
        'username',
        'password',
        'filter',
        'base',
    ]

    returnables = [
        'parent',
        'ip',
        'destination',
        'port',
        'interval',
        'timeout',
        'time_until_up',
        'description',
        'security',
        'debug',
        'mandatory_attributes',
        'chase_referrals',
        'manual_resume',
        'target_username',
        'filter',
        'base',
    ]

    updatables = [
        'destination',
        'interval',
        'timeout',
        'time_until_up',
        'description',
        'security',
        'debug',
        'mandatory_attributes',
        'chase_referrals',
        'manual_resume',
        'target_username',
        'target_password',
        'filter',
        'base',
    ]

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
    def mandatory_attributes(self):
        return flatten_boolean(self._values['mandatory_attributes'])

    @property
    def chase_referrals(self):
        return flatten_boolean(self._values['chase_referrals'])

    @property
    def debug(self):
        return flatten_boolean(self._values['debug'])

    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def security(self):
        if self._values['security'] in ['none', None]:
            return ''
        return self._values['security']


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
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']


class ModuleParameters(Parameters):
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
    def interval(self):
        if self._values['interval'] is None:
            return None
        if 1 > int(self._values['interval']) > 86400:
            raise F5ModuleError(
                "Interval value must be between 1 and 86400"
            )
        return int(self._values['interval'])

    @property
    def type(self):
        return 'ldap'

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
    @property
    def manual_resume(self):
        if self._values['manual_resume'] is None:
            return None
        if self._values['manual_resume'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def manual_resume(self):
        return flatten_boolean(self._values['manual_resume'])

    @property
    def ip(self):
        ip, port = self._values['destination'].split(':')
        return ip

    @property
    def port(self):
        ip, port = self._values['destination'].split(':')
        return int(port)


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
    def target_password(self):
        if self.want.target_password != self.have.target_password:
            if self.want.update_password == 'always':
                result = self.want.target_password
                return result

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

    def _set_default_creation_values(self):
        if self.want.ip is None:
            self.want.update({'ip': '*'})
        if self.want.port is None:
            self.want.update({'port': '*'})

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/ldap/{2}".format(
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/ldap/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/ldap/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/ldap/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/monitor/ldap/{2}".format(
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
            parent=dict(default='/Common/ldap'),
            ip=dict(),
            description=dict(),
            port=dict(),
            interval=dict(type='int'),
            timeout=dict(type='int'),
            target_username=dict(),
            target_password=dict(no_log=True),
            debug=dict(type='bool'),
            security=dict(
                choices=['none', 'ssl', 'tls']
            ),
            manual_resume=dict(type='bool'),
            time_until_up=dict(type='int'),
            up_interval=dict(type='int'),
            filter=dict(),
            base=dict(),
            mandatory_attributes=dict(type='bool'),
            chase_referrals=dict(type='bool'),
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
