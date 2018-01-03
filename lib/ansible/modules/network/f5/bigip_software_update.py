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
module: bigip_software_update
short_description: Manage the software update settings of a BIG-IP
description:
  - Manage the software update settings of a BIG-IP.
version_added: "2.5"
options:
  auto_check:
    description:
      - Specifies whether to automatically check for updates on the F5
        Networks downloads server.
    type: bool
  auto_phone_home:
    description:
      - Specifies whether to automatically send phone home data to the
        F5 Networks PhoneHome server.
    type: bool
  frequency:
    description:
      - Specifies the schedule for the automatic update check.
    choices:
      - daily
      - monthly
      - weekly
notes:
  - Requires the f5-sdk Python package on the host This is as easy as
    C(pip install f5-sdk)
extends_documentation_fragment: f5
requirements:
  - f5-sdk >= 3.0.6
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Enable automatic update checking
  bigip_software_update:
    auto_check: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Disable automatic update checking and phoning home
  bigip_software_update:
    auto_check: no
    auto_phone_home: no
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
auto_check:
  description: Whether the system checks for updates automatically.
  returned: changed
  type: bool
  sample: True
auto_phone_home:
  description: Whether the system automatically sends phone home data.
  returned: changed
  type: bool
  sample: True
frequency:
  description: Frequency of auto update checks
  returned: changed
  type: string
  sample: weekly
'''

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'autoCheck': 'auto_check',
        'autoPhonehome': 'auto_phone_home'
    }

    api_attributes = [
        'autoCheck', 'autoPhonehome', 'frequency'
    ]

    updatables = [
        'auto_check', 'auto_phone_home', 'frequency'
    ]

    returnables = [
        'auto_check', 'auto_phone_home', 'frequency'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class ApiParameters(Parameters):
    @property
    def auto_check(self):
        if self._values['auto_check'] is None:
            return None
        return self._values['auto_check']


class ModuleParameters(Parameters):
    @property
    def auto_check(self):
        if self._values['auto_check'] is None:
            return None
        elif self._values['auto_check'] is True:
            return 'enabled'
        else:
            return 'disabled'

    @property
    def auto_phone_home(self):
        if self._values['auto_phone_home'] is None:
            return None
        elif self._values['auto_phone_home'] is True:
            return 'enabled'
        else:
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
    def auto_check(self):
        if self._values['auto_check'] == 'enabled':
            return True
        elif self._values['auto_check'] == 'disabled':
            return False

    @property
    def auto_phone_home(self):
        if self._values['auto_phone_home'] == 'enabled':
            return True
        elif self._values['auto_phone_home'] == 'disabled':
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


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = ModuleParameters(self.client.module.params)
        self.changes = UsableChanges()

    def exec_module(self):
        result = dict()

        try:
            changed = self.update()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(self.changes.to_return())
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
            self.changes = UsableChanges(changed)
            return True
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
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        result = self.client.api.tm.sys.software.update.load()
        result.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.software.update.load()
        result = resource.attrs
        return ApiParameters(result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            auto_check=dict(
                type='bool'
            ),
            auto_phone_home=dict(
                type='bool'
            ),
            frequency=dict(
                choices=['daily', 'monthly', 'weekly']
            )
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
