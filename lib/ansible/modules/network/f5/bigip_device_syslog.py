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
module: bigip_device_syslog
short_description: Manage system-level syslog settings on BIG-IP
description:
  - Manage system-level syslog settings on BIG-IP.
version_added: 2.8
options:
  auth_priv_from:
    description:
      - Specifies the lowest level of messages about user authentication
        to include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  auth_priv_to:
    description:
      - Specifies the highest level of messages about user authentication
        to include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  console_log:
    description:
      - Enables or disables logging emergency syslog messages to the
        console.
    type: bool
  cron_from:
    description:
      - Specifies the lowest level of messages about time-based scheduling
        to include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  cron_to:
    description:
      - Specifies the highest level of messages about time-based
        scheduling to include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  daemon_from:
    description:
      - Specifies the lowest level of messages about daemon performance to
        include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  daemon_to:
    description:
      - Specifies the highest level of messages about daemon performance
        to include in the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  include:
    description:
      - Syslog-NG configuration to include in the device syslog config.
    type: str
  iso_date:
    description:
      - Enables or disables the ISO date format for messages in the log
        files.
    type: bool
  kern_from:
    description:
      - Specifies the lowest level of kernel messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  kern_to:
    description:
      - Specifies the highest level of kernel messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  local6_from:
    description:
      - Specifies the lowest error level for messages from the local6
        facility to include in the log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  local6_to:
    description:
      - Specifies the highest error level for messages from the local6
        facility to include in the log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  mail_from:
    description:
      - Specifies the lowest level of mail log messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  mail_to:
    description:
      - Specifies the highest level of mail log messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  messages_from:
    description:
      - Specifies the lowest level of system messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  messages_to:
    description:
      - Specifies the highest level of system messages to include in the
        system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  user_log_from:
    description:
      - Specifies the lowest level of user account messages to include in
        the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
  user_log_to:
    description:
      - Specifies the highest level of user account messages to include in
        the system log.
    type: str
    choices:
      - alert
      - crit
      - debug
      - emerg
      - err
      - info
      - notice
      - warning
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a syslog config
  bigip_device_syslog:
    name: foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
auth_priv_from:
  description: The new lowest user authentication logging level
  returned: changed
  type: str
  sample: alert
auth_priv_to:
  description: The new highest user authentication logging level.
  returned: changed
  type: str
  sample: emerg
console_log:
  description: Whether logging to console is enabled or not.
  returned: changed
  type: bool
  sample: yes
iso_date:
  description: Whether ISO date format in logs is enabled or not
  returned: changed
  type: bool
  sample: no
cron_from:
  description: The new lowest time-based scheduling logging level.
  returned: changed
  type: str
  sample: emerg
cron_to:
  description: The new highest time-based scheduling logging level.
  returned: changed
  type: str
  sample: alert
daemon_from:
  description: The new lowest daemon performance logging level.
  returned: changed
  type: str
  sample: alert
daemon_to:
  description: The new highest daemon performance logging level.
  returned: changed
  type: str
  sample: alert
include:
  description: The new extra syslog-ng configuration to include in syslog config.
  returned: changed
  type: str
  sample: "filter f_remote_syslog { not (facility(local6)) };"
kern_from:
  description: The new lowest kernel messages logging level.
  returned: changed
  type: str
  sample: alert
kern_to:
  description: The new highest kernel messages logging level.
  returned: changed
  type: str
  sample: alert
local6_from:
  description: The new lowest local6 facility logging level.
  returned: changed
  type: str
  sample: alert
local6_to:
  description: The new highest local6 facility logging level.
  returned: changed
  type: str
  sample: alert
mail_from:
  description: The new lowest mail log logging level.
  returned: changed
  type: str
  sample: alert
mail_to:
  description: The new highest mail log logging level.
  returned: changed
  type: str
  sample: alert
messages_from:
  description: The new lowest system logging level.
  returned: changed
  type: str
  sample: alert
messages_to:
  description: The new highest system logging level.
  returned: changed
  type: str
  sample: alert
user_log_from:
  description: The new lowest user account logging level.
  returned: changed
  type: str
  sample: alert
user_log_to:
  description: The new highest user account logging level.
  returned: changed
  type: str
  sample: alert
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'authPrivFrom': 'auth_priv_from',
        'authPrivTo': 'auth_priv_to',
        'consoleLog': 'console_log',
        'cronFrom': 'cron_from',
        'cronTo': 'cron_to',
        'daemonFrom': 'daemon_from',
        'daemonTo': 'daemon_to',
        'isoDate': 'iso_date',
        'kernFrom': 'kern_from',
        'kernTo': 'kern_to',
        'local6From': 'local6_from',
        'local6To': 'local6_to',
        'mailFrom': 'mail_from',
        'mailTo': 'mail_to',
        'messagesFrom': 'messages_from',
        'messagesTo': 'messages_to',
        'userLogFrom': 'user_log_from',
        'userLogTo': 'user_log_to',
    }

    api_attributes = [
        'include',
        'authPrivFrom',
        'authPrivTo',
        'consoleLog',
        'cronFrom',
        'cronTo',
        'daemonFrom',
        'daemonTo',
        'isoDate',
        'kernFrom',
        'kernTo',
        'local6From',
        'local6To',
        'mailFrom',
        'mailTo',
        'messagesFrom',
        'messagesTo',
        'userLogFrom',
        'userLogTo',
    ]

    returnables = [
        'include',
        'auth_priv_from',
        'auth_priv_to',
        'console_log',
        'cron_from',
        'cron_to',
        'daemon_from',
        'daemon_to',
        'iso_date',
        'kern_from',
        'kern_to',
        'local6_from',
        'local6_to',
        'mail_from',
        'mail_to',
        'messages_from',
        'messages_to',
        'user_log_from',
        'user_log_to',
    ]

    updatables = [
        'include',
        'auth_priv_from',
        'auth_priv_to',
        'console_log',
        'cron_from',
        'cron_to',
        'daemon_from',
        'daemon_to',
        'iso_date',
        'kern_from',
        'kern_to',
        'local6_from',
        'local6_to',
        'mail_from',
        'mail_to',
        'messages_from',
        'messages_to',
        'user_log_from',
        'user_log_to',
    ]

    @property
    def console_log(self):
        return flatten_boolean(self._values['console_log'])

    @property
    def iso_date(self):
        return flatten_boolean(self._values['iso_date'])


class ApiParameters(Parameters):
    @property
    def include(self):
        if self._values['include'] in [None, 'none']:
            return None
        return self._values['include']


class ModuleParameters(Parameters):
    @property
    def include(self):
        if self._values['include'] is None:
            return None
        if self._values['include'] in ['', 'none']:
            return ''
        return self._values['include'].replace('"', "'")


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
    def console_log(self):
        if self._values['console_log'] is None:
            return None
        elif self._values['console_log'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def iso_date(self):
        if self._values['iso_date'] is None:
            return None
        elif self._values['iso_date'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def console_log(self):
        return flatten_boolean(self._values['console_log'])

    @property
    def iso_date(self):
        return flatten_boolean(self._values['iso_date'])


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
    def include(self):
        return cmp_str_with_none(self.want.include, self.have.include)


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
        result = dict()

        changed = self.present()

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
        return self.update()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/syslog".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        uri = "https://{0}:{1}/mgmt/tm/sys/syslog".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        levels = [
            'alert', 'crit', 'debug', 'emerg', 'err', 'info', 'notice', 'warning'
        ]

        argument_spec = dict(
            auth_priv_from=dict(choices=levels),
            auth_priv_to=dict(choices=levels),
            console_log=dict(type='bool'),
            cron_from=dict(choices=levels),
            cron_to=dict(choices=levels),
            daemon_from=dict(choices=levels),
            daemon_to=dict(choices=levels),
            include=dict(),
            iso_date=dict(type='bool'),
            kern_from=dict(choices=levels),
            kern_to=dict(choices=levels),
            local6_from=dict(choices=levels),
            local6_to=dict(choices=levels),
            mail_from=dict(choices=levels),
            mail_to=dict(choices=levels),
            messages_from=dict(choices=levels),
            messages_to=dict(choices=levels),
            user_log_from=dict(choices=levels),
            user_log_to=dict(choices=levels),
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
