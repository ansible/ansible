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
module: bigip_firewall_global_rules
short_description: Manage AFM global rule settings on BIG-IP
description:
  - Configures the global network firewall rules. These firewall rules are
    applied to all packets except those going through the management
    interface. They are applied first, before any firewall rules for the
    packet's virtual server, route domain, and/or self IP.
version_added: 2.8
options:
  enforced_policy:
    description:
      - Specifies an enforced firewall policy.
      - C(enforced_policy) rules are enforced globally.
    type: str
  service_policy:
    description:
      - Specifies a service policy that would apply to traffic globally.
      - The service policy is applied to all flows, provided if there are
        no other context specific service policy configuration that
        overrides the global service policy. For example, when a service
        policy is configured both at a global level, as well as on a
        firewall rule, and a flow matches the rule, the more specific
        service policy configuration in the rule will override the service
        policy setting at the global level.
      - The service policy associated here can be created using the
        C(bigip_service_policy) module.
    type: str
  staged_policy:
    description:
      - Specifies a staged firewall policy.
      - C(staged_policy) rules are not enforced while all the visibility
        aspects namely statistics, reporting and logging function as if
        the staged-policy rules were enforced globally.
    type: str
  description:
    description:
      - Description for the global list of firewall rules.
    type: str
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Change enforced policy in AFM global rules
  bigip_firewall_global_rules:
    enforced_policy: enforcing1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
enforced_policy:
  description: The new global Enforced Policy.
  returned: changed
  type: str
  sample: /Common/enforced1
service_policy:
  description: The new global Service Policy.
  returned: changed
  type: str
  sample: /Common/service1
staged_policy:
  description: The new global Staged Policy.
  returned: changed
  type: str
  sample: /Common/staged1
description:
  description: The new description.
  returned: changed
  type: str
  sample: My description
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'enforcedPolicy': 'enforced_policy',
        'servicePolicy': 'service_policy',
        'stagedPolicy': 'staged_policy',
    }

    api_attributes = [
        'enforcedPolicy',
        'servicePolicy',
        'stagedPolicy',
        'description',
    ]

    returnables = [
        'enforced_policy',
        'service_policy',
        'staged_policy',
        'description',
    ]

    updatables = [
        'enforced_policy',
        'service_policy',
        'staged_policy',
        'description',
    ]


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']


class ModuleParameters(Parameters):
    @property
    def enforced_policy(self):
        if self._values['enforced_policy'] is None:
            return None
        if self._values['enforced_policy'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['enforced_policy'])

    @property
    def service_policy(self):
        if self._values['service_policy'] is None:
            return None
        if self._values['service_policy'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['service_policy'])

    @property
    def staged_policy(self):
        if self._values['staged_policy'] is None:
            return None
        if self._values['staged_policy'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['staged_policy'])

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
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)

    @property
    def enforced_policy(self):
        return cmp_str_with_none(self.want.enforced_policy, self.have.enforced_policy)

    @property
    def staged_policy(self):
        return cmp_str_with_none(self.want.staged_policy, self.have.staged_policy)

    @property
    def service_policy(self):
        return cmp_str_with_none(self.want.service_policy, self.have.service_policy)


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
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/global-rules".format(
            self.client.provider['server'],
            self.client.provider['server_port']
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
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/global-rules".format(
            self.client.provider['server'],
            self.client.provider['server_port']
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
            enforced_policy=dict(),
            service_policy=dict(),
            staged_policy=dict(),
            description=dict(),
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
