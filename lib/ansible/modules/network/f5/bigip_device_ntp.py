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
module: bigip_device_ntp
short_description: Manage NTP servers on a BIG-IP
description:
  - Manage NTP servers on a BIG-IP.
version_added: 2.2
options:
  ntp_servers:
    description:
      - A list of NTP servers to set on the device. At least one of C(ntp_servers)
        or C(timezone) is required.
    type: list
  state:
    description:
      - The state of the NTP servers on the system. When C(present), guarantees
        that the NTP servers are set on the system. When C(absent), removes the
        specified NTP servers from the device configuration.
    type: str
    choices:
      - absent
      - present
    default: present
  timezone:
    description:
      - The timezone to set for NTP lookups. At least one of C(ntp_servers) or
        C(timezone) is required.
    type: str
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Set NTP server
  bigip_device_ntp:
    ntp_servers:
      - 192.0.2.23
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set timezone
  bigip_device_ntp:
    timezone: America/Los_Angeles
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
ntp_servers:
  description: The NTP servers that were set on the device
  returned: changed
  type: list
  sample: ["192.0.2.23", "192.0.2.42"]
timezone:
  description: The timezone that was set on the device
  returned: changed
  type: str
  sample: true
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_empty_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_empty_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'servers': 'ntp_servers',
    }

    api_attributes = [
        'servers', 'timezone',
    ]

    updatables = [
        'ntp_servers', 'timezone',
    ]

    returnables = [
        'ntp_servers', 'timezone',
    ]

    absentables = [
        'ntp_servers',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def ntp_servers(self):
        ntp_servers = self._values['ntp_servers']
        if ntp_servers is None:
            return None
        if is_empty_list(ntp_servers):
            return []
        return ntp_servers


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
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
    def ntp_servers(self):
        state = self.want.state
        if self.want.ntp_servers is None:
            return None
        if state == 'absent':
            if self.have.ntp_servers is None and self.want.ntp_servers:
                return None
            if set(self.want.ntp_servers) == set(self.have.ntp_servers):
                return []
            if set(self.want.ntp_servers) != set(self.have.ntp_servers):
                return list(set(self.want.ntp_servers).difference(self.have.ntp_servers))
        if not self.want.ntp_servers:
            if self.have.ntp_servers is None:
                return None
            if self.have.ntp_servers is not None:
                return self.want.ntp_servers
        if self.have.ntp_servers is None:
            return self.want.ntp_servers
        if set(self.want.ntp_servers) != set(self.have.ntp_servers):
            return self.want.ntp_servers


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

    def _absent_changed_options(self):
        diff = Difference(self.want, self.have)
        absentables = Parameters.absentables
        changed = dict()
        for k in absentables:
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
            changed = self.update()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)

        if self.module._diff and self.have:
            result['diff'] = self.make_diff()

        result.update(dict(changed=changed))
        self._announce_deprecations(result)

        return result

    def _grab_attr(self, item):
        result = dict()
        updatables = Parameters.updatables
        for k in updatables:
            if getattr(item, k) is not None:
                result[k] = getattr(item, k)
        return result

    def make_diff(self):
        result = dict(before=self._grab_attr(self.have), after=self._grab_attr(self.want))
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def should_absent(self):
        result = self._absent_changed_options()
        if result:
            return True
        return False

    def absent(self):
        self.have = self.read_current_from_device()
        if not self.should_absent():
            return False
        if self.module.check_mode:
            return True
        self.absent_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/ntp/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/ntp/".format(
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

    def absent_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/ntp/".format(
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


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            ntp_servers=dict(
                type='list',
            ),
            timezone=dict(),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)

        self.required_one_of = [
            ['ntp_servers', 'timezone']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_one_of=spec.required_one_of
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
