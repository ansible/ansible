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
module: bigip_firewall_rule_list
short_description: Manage AFM security firewall policies on a BIG-IP
description:
  - Manages AFM security firewall policies on a BIG-IP.
version_added: 2.7
options:
  name:
    description:
      - The name of the policy to create.
    type: str
    required: True
  description:
    description:
      - The description to attach to the policy.
      - This parameter is only supported on versions of BIG-IP >= 12.1.0. On earlier
        versions it will simply be ignored.
    type: str
  state:
    description:
      - When C(state) is C(present), ensures that the rule list exists.
      - When C(state) is C(absent), ensures that the rule list is removed.
    type: str
    choices:
      - present
      - absent
    default: present
  rules:
    description:
      - Specifies a list of rules that you want associated with this policy.
        The order of this list is the order they will be evaluated by BIG-IP.
        If the specified rules do not exist (for example when creating a new
        policy) then they will be created.
      - Rules specified here, if they do not exist, will be created with "default deny"
        behavior. It is expected that you follow-up this module with the actual
        configuration for these rules.
      - The C(bigip_firewall_rule) module can be used to also create, as well as
        edit, existing and new rules.
    type: list
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a basic policy with some rule stubs
  bigip_firewall_rule_list:
    name: foo
    rules:
      - rule1
      - rule2
      - rule3
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the policy.
  returned: changed
  type: str
  sample: My firewall policy
rules:
  description: The list of rules, in the order that they are evaluated, on the device.
  returned: changed
  type: list
  sample: ['rule1', 'rule2', 'rule3']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'rulesReference': 'rules'
    }

    api_attributes = [
        'description'
    ]

    returnables = [
        'description',
        'rules',
    ]

    updatables = [
        'description',
        'rules'
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


class ModuleParameters(Parameters):
    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        # In case rule values are unicode (as they may be coming from the API
        result = [str(x) for x in self._values['rules']]
        return result


class ApiParameters(Parameters):
    @property
    def rules(self):
        result = []
        if self._values['rules'] is None or 'items' not in self._values['rules']:
            return []
        for idx, item in enumerate(self._values['rules']['items']):
            result.append(dict(item=item['fullPath'], order=idx))
        result = [x['item'] for x in sorted(result, key=lambda k: k['order'])]
        return result


class Changes(Parameters):
    pass


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
    def rules(self):
        if self.want.rules is None:
            return None
        if self.have.rules is None:
            return self.want.rules
        if set(self.want.rules) != set(self.have.rules):
            return self.want.rules


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

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/".format(
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
        if self.want.rules:
            self._upsert_policy_rules_on_device()
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        if params:
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
            return response['selfLink']
        if self.changes.rules is not None:
            self._upsert_policy_rules_on_device()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True
        raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/?expandSubcollections=true".format(
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

    def rule_exists(self, rule):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
            rule.replace('/', '_')
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_default_rule_on_device(self, rule):
        params = dict(
            name=rule.replace('/', '_'),
            action='reject',
            # Adding items to the end of the list causes the list of rules to match
            # what the user specified in the original list.
            placeAfter='last',
        )
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
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

    def remove_rule_from_device(self, rule):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
            rule.replace('/', '_'),
        )
        # this response returns no payload
        resp = self.client.api.delete(uri)
        if resp.status in [400, 403]:
            raise F5ModuleError(resp.content)

    def move_rule_to_front(self, rule):
        params = dict(
            placeAfter='last'
        )
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/rule-list/{2}/rules/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name),
            rule.replace('/', '_')
        )
        resp = self.client.api.patch(uri, json=params)
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

    def _upsert_policy_rules_on_device(self):
        rules = self.changes.rules
        if rules is None:
            rules = []
        self._remove_rule_difference(rules)

        for idx, rule in enumerate(rules):
            if not self.rule_exists(rule):
                self.create_default_rule_on_device(rule)
        for idx, rule in enumerate(rules):
            self.move_rule_to_front(rule)

    def _remove_rule_difference(self, rules):
        if rules is None or self.have.rules is None:
            return
        have_rules = set(self.have.rules)
        want_rules = set(rules)
        removable = have_rules.difference(want_rules)
        for remove in removable:
            self.remove_rule_from_device(remove)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            rules=dict(type='list'),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
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
