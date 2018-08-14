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
module: bigip_policy
short_description: Manage general policy configuration on a BIG-IP
description:
  - Manages general policy configuration on a BIG-IP. This module is best
    used in conjunction with the C(bigip_policy_rule) module. This module
    can handle general configuration like setting the draft state of the policy,
    the description, and things unrelated to the policy rules themselves.
    It is also the first module that should be used when creating rules as
    the C(bigip_policy_rule) module requires a policy parameter.
version_added: 2.5
options:
  description:
    description:
      - The description to attach to the policy.
      - This parameter is only supported on versions of BIG-IP >= 12.1.0. On earlier
        versions it will simply be ignored.
  name:
    description:
      - The name of the policy to create.
    required: True
  state:
    description:
      - When C(state) is C(present), ensures that the policy exists and is
        published. When C(state) is C(absent), ensures that the policy is removed,
        even if it is currently drafted.
      - When C(state) is C(draft), ensures that the policy exists and is drafted.
        When modifying rules, it is required that policies first be in a draft.
      - Drafting is only supported on versions of BIG-IP >= 12.1.0. On versions
        prior to that, specifying a C(state) of C(draft) will raise an error.
    choices:
      - present
      - absent
      - draft
    default: present
  strategy:
    description:
      - Specifies the method to determine which actions get executed in the
        case where there are multiple rules that match. When creating new
        policies, the default is C(first).
      - This module does not allow you to specify the C(best) strategy to use.
        It will choose the system default (C(/Common/best-match)) for you instead.
    choices:
      - first
      - all
      - best
  rules:
    description:
      - Specifies a list of rules that you want associated with this policy.
        The order of this list is the order they will be evaluated by BIG-IP.
        If the specified rules do not exist (for example when creating a new
        policy) then they will be created.
      - The C(conditions) for a default rule are C(all).
      - The C(actions) for a default rule are C(ignore).
      - The C(bigip_policy_rule) module can be used to create and edit existing
        and new rules.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create policy which is immediately published
  bigip_policy:
    name: Policy-Foo
    state: present
  delegate_to: localhost

- name: Add a rule to the new policy - Immediately published
  bigip_policy_rule:
    policy: Policy-Foo
    name: ABC
    conditions:
      - type: http_uri
        path_starts_with:
          - /ABC
          - foo
          - bar
        path_ends_with:
          - baz
    actions:
      - forward: yes
        select: yes
        pool: pool-svrs

- name: Add multiple rules to the new policy - Added in the order they are specified
  bigip_policy_rule:
    policy: Policy-Foo
    name: "{{ item.name }}"
    conditions: "{{ item.conditions }}"
    actions: "{{ item.actions }}"
  with_items:
    - name: rule1
      actions:
        - type: forward
          pool: pool-svrs
      conditions:
        - type: http_uri
          path_starts_with: /euro
    - name: HomePage
      actions:
        - type: forward
          pool: pool-svrs
      conditions:
        - type: http_uri
          path_starts_with: /HomePage/

- name: Create policy specify default rules - Immediately published
  bigip_policy:
    name: Policy-Bar
    state: present
    rules:
      - rule1
      - rule2
      - rule3

- name: Create policy specify default rules - Left in a draft
  bigip_policy:
    name: Policy-Baz
    state: draft
    rules:
      - rule1
      - rule2
      - rule3
'''

RETURN = r'''
strategy:
  description: The new strategy set on the policy.
  returned: changed and success
  type: int
  sample: first-match
description:
  description:
    - The new description of the policy.
    - This value is only returned for BIG-IP devices >= 12.1.0.
  returned: changed and success
  type: string
  sample: This is my description
rules:
  description: List of the rules, and their order, applied to the policy.
  returned: changed and success
  type: list
  sample: ['/Common/rule1', '/Common/rule2']
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

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
    from f5.sdk_exception import NonExtantPolicyRule
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    @property
    def strategy(self):
        if self._values['strategy'] is None:
            return None

        # Look for 'first' from Ansible or REST
        elif self._values['strategy'] == 'first':
            return self._get_builtin_strategy('first')
        elif 'first-match' in self._values['strategy']:
            return str(self._values['strategy'])

        # Look for 'all' from Ansible or REST
        elif self._values['strategy'] == 'all':
            return self._get_builtin_strategy('all')
        elif 'all-match' in self._values['strategy']:
            return str(self._values['strategy'])

        else:
            # Look for 'best' from Ansible or REST
            if self._values['strategy'] == 'best':
                return self._get_builtin_strategy('best')
            elif 'best-match' in self._values['strategy']:
                return str(self._values['strategy'])
            else:
                # These are custom strategies. The strategy may include the
                # partition, but if it does not, then we add the partition
                # that is provided to the module.
                return self._get_custom_strategy_name()

    def _get_builtin_strategy(self, strategy):
        return '/Common/{0}-match'.format(strategy)

    def _get_custom_strategy_name(self):
        strategy = self._values['strategy']
        if re.match(r'(\/[a-zA-Z_0-9.-]+){2}', strategy):
            return strategy
        elif re.match(r'[a-zA-Z_0-9.-]+', strategy):
            return '/{0}/{1}'.format(self.partition, strategy)
        else:
            raise F5ModuleError(
                "The provided strategy name is invalid!"
            )

    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        # In case rule values are unicode (as they may be coming from the API
        result = [str(x) for x in self._values['rules']]
        return result


class SimpleParameters(Parameters):
    api_attributes = [
        'strategy'
    ]

    updatables = [
        'strategy', 'rules'
    ]

    returnables = [
        'strategy', 'rules'
    ]


class ComplexParameters(Parameters):
    api_attributes = [
        'strategy', 'description'
    ]

    updatables = [
        'strategy', 'description', 'rules'
    ]

    returnables = [
        'strategy', 'description', 'rules'
    ]


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__deprecated', [])
        if self.have:
            warnings += self.have._values.get('__deprecated', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _announce_warnings(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warning', [])
        if self.have:
            warnings += self.have._values.get('__warning', [])
        for warning in warnings:
            self.module.warn(warning['msg'])

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

    def _validate_creation_parameters(self):
        if self.want.strategy is None:
            self.want.update(dict(strategy='first'))

    def _get_rule_names(self, resource):
        rules = resource.rules_s.get_collection()
        rules.sort(key=lambda x: x.ordinal)
        result = [x.name for x in rules]
        return result

    def _upsert_policy_rules_on_device(self, policy):
        rules = self.changes.rules
        if rules is None:
            rules = []
        for idx, rule in enumerate(rules):
            try:
                resource = policy.rules_s.rules.load(name=rule)
                if int(resource.ordinal) != idx:
                    resource.modify(ordinal=idx)
            except NonExtantPolicyRule:
                policy.rules_s.rules.create(name=rule, ordinal=idx)
        self._remove_rule_difference(rules, policy)

    def _remove_rule_difference(self, rules, policy=None):
        if not rules or not self.have.rules:
            return
        have_rules = set(self.have.rules)
        want_rules = set(rules)
        removable = have_rules.difference(want_rules)
        for remove in removable:
            resource = policy.rules_s.rules.load(name=remove)
            resource.delete()


class SimpleManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(SimpleManager, self).__init__(**kwargs)
        self.want = SimpleParameters(params=self.module.params)
        self.have = SimpleParameters()
        self.changes = SimpleChanges()

    def _set_changed_options(self):
        changed = {}
        for key in SimpleParameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = SimpleChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = SimpleParameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                changed[k] = change
        if changed:
            self.changes = SimpleChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == 'draft':
                raise F5ModuleError(
                    "The 'draft' status is not available on BIG-IP versions < 12.1.0"
                )
            if state == 'present':
                changed = self.present()
            elif state == 'absent':
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        self._announce_warnings()
        return result

    def read_current_from_device(self):
        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        rules = self._get_rule_names(resource)
        result = SimpleParameters(params=resource.attrs)
        result.update(dict(rules=rules))
        return result

    def exists(self):
        result = self.client.api.tm.ltm.policys.policy.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.changes.api_params()

        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if params:
            resource.modify(**params)
        self._upsert_policy_rules_on_device(resource)

    def create(self):
        self._validate_creation_parameters()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.want.api_params()

        params = dict(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )
        resource = self.client.api.tm.ltm.policys.policy.create(**params)
        self._upsert_policy_rules_on_device(resource)
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the policy")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ComplexManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(ComplexManager, self).__init__(**kwargs)
        self.want = ComplexParameters(params=self.module.params)
        self.have = ComplexParameters()
        self.changes = ComplexChanges()

    def _set_changed_options(self):
        changed = {}
        for key in ComplexParameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = ComplexChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = ComplexParameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                changed[k] = change
        if changed:
            self.changes = ComplexChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ["present", "draft"]:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def should_update(self):
        result = self._update_changed_options()
        drafted = self.draft_status_changed()
        if any(x is True for x in [result, drafted]):
            return True
        return False

    def draft_status_changed(self):
        if self.draft_exists() and self.want.state == 'draft':
            drafted = False
        elif not self.draft_exists() and self.want.state == 'present':
            drafted = False
        else:
            drafted = True
        return drafted

    def present(self):
        if self.draft_exists() or self.policy_exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.draft_exists() or self.policy_exists():
            changed = self.remove()
        return changed

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.draft_exists() or self.policy_exists():
            raise F5ModuleError("Failed to delete the policy")
        return True

    def remove_from_device(self):
        if self.draft_exists():
            resource = self.client.api.tm.ltm.policys.policy.load(
                name=self.want.name,
                partition=self.want.partition,
                subPath='Drafts'
            )
            resource.delete()
        if self.policy_exists():
            resource = self.client.api.tm.ltm.policys.policy.load(
                name=self.want.name,
                partition=self.want.partition
            )
            resource.delete()

    def read_current_from_device(self):
        if self.draft_exists():
            resource = self.client.api.tm.ltm.policys.policy.load(
                name=self.want.name,
                partition=self.want.partition,
                subPath='Drafts'
            )
        else:
            resource = self.client.api.tm.ltm.policys.policy.load(
                name=self.want.name,
                partition=self.want.partition
            )

        rules = self._get_rule_names(resource)
        result = ComplexParameters(params=resource.attrs)
        result.update(dict(rules=rules))
        return result

    def policy_exists(self):
        params = dict(
            name=self.want.name,
            partition=self.want.partition
        )
        result = self.client.api.tm.ltm.policys.policy.exists(**params)
        return result

    def draft_exists(self):
        params = dict(
            name=self.want.name,
            partition=self.want.partition,
            subPath='Drafts'
        )
        result = self.client.api.tm.ltm.policys.policy.exists(**params)
        return result

    def _create_new_policy_draft(self):
        params = self.want.api_params()
        params = dict(
            name=self.want.name,
            partition=self.want.partition,
            subPath='Drafts',
            **params
        )
        self.client.api.tm.ltm.policys.policy.create(**params)
        return True

    def _create_existing_policy_draft(self):
        params = dict(
            name=self.want.name,
            partition=self.want.partition,
        )
        resource = self.client.api.tm.ltm.policys.policy.load(**params)
        resource.draft()
        return True

    def update_on_device(self):
        params = self.changes.api_params()

        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.name,
            partition=self.want.partition,
            subPath='Drafts'
        )
        if params:
            resource.modify(**params)
        self._upsert_policy_rules_on_device(resource)

    def publish(self):
        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.name,
            partition=self.want.partition,
            subPath='Drafts'
        )
        resource.publish()
        return True

    def create(self):
        self._validate_creation_parameters()

        self._set_changed_options()
        if self.module.check_mode:
            return True

        if not self.draft_exists():
            self._create_new_policy_draft()

        # Because we always need to modify drafts, "creating on the device"
        # is actually identical to just updating.
        self.update_on_device()

        if self.want.state == 'draft':
            return True
        else:
            return self.publish()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True

        if not self.draft_exists():
            self._create_existing_policy_draft()

        if self._update_changed_options():
            self.update_on_device()

        if self.want.state == 'draft':
            return True
        else:
            return self.publish()


class SimpleChanges(SimpleParameters):
    api_attributes = [
        'strategy'
    ]

    updatables = [
        'strategy', 'rules'
    ]

    returnables = [
        'strategy', 'rules'
    ]


class ComplexChanges(ComplexParameters):
    api_attributes = [
        'strategy', 'description'
    ]

    updatables = [
        'strategy', 'description', 'rules'
    ]

    returnables = [
        'strategy', 'description', 'rules'
    ]


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
        if self.want.rules != self.have.rules:
            return self.want.rules


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        if self.version_is_less_than_12():
            manager = self.get_manager('simple')
        else:
            manager = self.get_manager('complex')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'simple':
            return SimpleManager(**self.kwargs)
        elif type == 'complex':
            return ComplexManager(**self.kwargs)

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True
            ),
            description=dict(),
            rules=dict(type='list'),
            strategy=dict(
                choices=['first', 'all', 'best']
            ),
            state=dict(
                default='present',
                choices=['absent', 'present', 'draft']
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
