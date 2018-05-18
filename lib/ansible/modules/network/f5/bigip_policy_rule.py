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
module: bigip_policy_rule
short_description: Manage LTM policy rules on a BIG-IP
description:
  - This module will manage LTM policy rules on a BIG-IP.
version_added: 2.5
options:
  description:
    description:
      - Description of the policy rule.
  actions:
    description:
      - The actions that you want the policy rule to perform.
      - The available attributes vary by the action, however, each action requires that
        a C(type) be specified.
      - These conditions can be specified in any order. Despite them being a list, the
        BIG-IP does not treat their order as anything special.
    suboptions:
      type:
        description:
          - The action type. This value controls what below options are required.
          - When C(type) is C(forward), will associate a given C(pool), or C(virtual)
            with this rule.
          - When C(type) is C(enable), will associate a given C(asm_policy) with
            this rule.
          - When C(type) is C(ignore), will remove all existing actions from this
            rule.
        required: true
        choices: ['forward', 'enable', 'ignore']
      pool:
        description:
          - Pool that you want to forward traffic to.
          - This parameter is only valid with the C(forward) type.
      virtual:
        description:
          - Virtual Server that you want to forward traffic to.
          - This parameter is only valid with the C(forward) type.
      asm_policy:
        description:
          - ASM policy to enable.
          - This parameter is only valid with the C(enable) type.
  policy:
    description:
      - The name of the policy that you want to associate this rule with.
    required: True
  name:
    description:
      - The name of the rule.
    required: True
  conditions:
    description:
      - A list of attributes that describe the condition.
      - See suboptions for details on how to construct each list entry.
      - The ordering of this list is important, the module will ensure the order is
        kept when modifying the task.
      - The suboption options listed below are not required for all condition types,
        read the description for more details.
      - These conditions can be specified in any order. Despite them being a list, the
        BIG-IP does not treat their order as anything special.
    suboptions:
      type:
        description:
          - The condition type. This value controls what below options are required.
          - When C(type) is C(http_uri), will associate a given C(path_begins_with_any)
            list of strings with which the HTTP URI should begin with. Any item in the
            list will provide a match.
          - When C(type) is C(all_traffic), will remove all existing conditions from
            this rule.
        required: True
        choices: [ 'http_uri', 'all_traffic' ]
      path_begins_with_any:
        description:
          - A list of strings of characters that the HTTP URI should start with.
          - This parameter is only valid with the C(http_uri) type.
  state:
    description:
      - When C(present), ensures that the key is uploaded to the device. When
        C(absent), ensures that the key is removed from the device. If the key
        is currently in use, the module will not be able to remove the key.
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
extends_documentation_fragment: f5
requirements:
  - BIG-IP >= v12.1.0
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create policies
  bigip_policy:
    name: Policy-Foo
    state: present
  delegate_to: localhost

- name: Add a rule to the new policy
  bigip_policy_rule:
    policy: Policy-Foo
    name: rule3
    conditions:
      - type: http_uri
        path_begins_with_any: /ABC
    actions:
      - type: forward
        pool: pool-svrs
  delegate_to: localhost

- name: Add multiple rules to the new policy
  bigip_policy_rule:
    policy: Policy-Foo
    name: "{{ item.name }}"
    conditions: "{{ item.conditions }}"
    actions: "{{ item.actions }}"
  delegate_to: localhost
  loop:
    - name: rule1
      actions:
        - type: forward
          pool: pool-svrs
      conditions:
        - type: http_uri
          path_starts_with: /euro
    - name: rule2
      actions:
        - type: forward
          pool: pool-svrs
      conditions:
        - type: http_uri
          path_starts_with: /HomePage/

- name: Remove all rules and confitions from the rule
  bigip_policy_rule:
    policy: Policy-Foo
    name: rule1
    conditions:
      - type: all_traffic
    actions:
      - type: ignore
  delegate_to: localhost
'''

RETURN = r'''
actions:
  description: The new list of actions applied to the rule
  returned: changed
  type: complex
  contains:
    type:
      description: The action type
      returned: changed
      type: string
      sample: forward
    pool:
      description: Pool for forward to
      returned: changed
      type: string
      sample: foo-pool
  sample: hash/dictionary of values
conditions:
  description: The new list of conditions applied to the rule.
  returned: changed
  type: complex
  contains:
    type:
      description: The condition type.
      returned: changed
      type: string
      sample: http_uri
    path_begins_with_any:
      description: List of strings that the URI begins with.
      returned: changed
      type: list
      sample: [foo, bar]
  sample: hash/dictionary of values
description:
  description: The new description of the rule.
  returned: changed
  type: string
  sample: My rule
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

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


class Parameters(AnsibleF5Parameters):
    api_map = {
        'actionsReference': 'actions',
        'conditionsReference': 'conditions'
    }
    api_attributes = [
        'description', 'actions', 'conditions'
    ]

    updatables = [
        'actions', 'conditions', 'description'
    ]

    returnable = [
        'description'
    ]

    @property
    def name(self):
        return self._values.get('name', None)

    @property
    def description(self):
        return self._values.get('description', None)

    @property
    def policy(self):
        if self._values['policy'] is None:
            return None
        return self._values['policy']


class ApiParameters(Parameters):
    def _remove_internal_keywords(self, resource):
        items = ['kind', 'generation', 'selfLink', 'poolReference']
        for item in items:
            try:
                del resource[item]
            except KeyError:
                pass

    @property
    def actions(self):
        result = []
        if self._values['actions'] is None or 'items' not in self._values['actions']:
            return [dict(type='ignore')]
        for item in self._values['actions']['items']:
            action = dict()
            self._remove_internal_keywords(item)
            if 'forward' in item:
                action.update(item)
                action['type'] = 'forward'
                del action['forward']
            elif 'enable' in item:
                action.update(item)
                action['type'] = 'enable'
                del action['enable']
            result.append(action)
        result = sorted(result, key=lambda x: x['name'])
        return result

    @property
    def conditions(self):
        result = []
        if self._values['conditions'] is None or 'items' not in self._values['conditions']:
            return [dict(type='all_traffic')]
        for item in self._values['conditions']['items']:
            action = dict()
            self._remove_internal_keywords(item)
            if 'httpUri' in item:
                action.update(item)
                action['type'] = 'http_uri'
                del action['httpUri']

                # Converts to common stringiness
                #
                # The tuple set "issubset" check that happens in the Difference
                # engine does not recognize that a u'foo' and 'foo' are equal "enough"
                # to consider them a subset. Therefore, we cast everything here to
                # whatever the common stringiness is.
                if 'values' in action:
                    action['values'] = [str(x) for x in action['values']]
            result.append(action)
        # Names contains the index in which the rule is at.
        result = sorted(result, key=lambda x: x['name'])
        return result


class ModuleParameters(Parameters):
    @property
    def actions(self):
        result = []
        if self._values['actions'] is None:
            return None
        for idx, item in enumerate(self._values['actions']):
            action = dict()
            if 'name' in item:
                action['name'] = str(item['name'])
            else:
                action['name'] = str(idx)
            if item['type'] == 'forward':
                self._handle_forward_action(action, item)
            elif item['type'] == 'enable':
                self._handle_enable_action(action, item)
            elif item['type'] == 'ignore':
                return [dict(type='ignore')]
            result.append(action)
        result = sorted(result, key=lambda x: x['name'])
        return result

    @property
    def conditions(self):
        result = []
        if self._values['conditions'] is None:
            return None
        for idx, item in enumerate(self._values['conditions']):
            action = dict()
            if 'name' in item:
                action['name'] = str(item['name'])
            else:
                action['name'] = str(idx)
            if item['type'] == 'http_uri':
                self._handle_http_uri_condition(action, item)
            elif item['type'] == 'all_traffic':
                return [dict(type='all_traffic')]
            result.append(action)
        result = sorted(result, key=lambda x: x['name'])
        return result

    def _handle_http_uri_condition(self, action, item):
        """Handle the nuances of the forwarding type

        Right now there is only a single type of forwarding that can be done. As that
        functionality expands, so-to will the behavior of this, and other, methods.
        Therefore, do not be surprised that the logic here is so rigid. It's deliberate.

        :param action:
        :param item:
        :return:
        """
        action['type'] = 'http_uri'
        if 'path_begins_with_any' not in item:
            raise F5ModuleError(
                "A 'path_begins_with_any' must be specified when the 'http_uri' type is used."
            )
        if isinstance(item['path_begins_with_any'], list):
            values = item['path_begins_with_any']
        else:
            values = [item['path_begins_with_any']]
        action.update(dict(
            path=True,
            startsWith=True,
            values=values
        ))

    def _handle_forward_action(self, action, item):
        """Handle the nuances of the forwarding type

        Right now there is only a single type of forwarding that can be done. As that
        functionality expands, so-to will the behavior of this, and other, methods.
        Therefore, do not be surprised that the logic here is so rigid. It's deliberate.

        :param action:
        :param item:
        :return:
        """
        action['type'] = 'forward'
        if not any(x for x in ['pool', 'virtual'] if x in item):
            raise F5ModuleError(
                "A 'pool' or 'virtual' must be specified when the 'forward' type is used."
            )
        if item.get('pool', None):
            action['pool'] = fq_name(self.partition, item['pool'])
        elif item.get('virtual', None):
            action['virtual'] = fq_name(self.partition, item['virtual'])

    def _handle_enable_action(self, action, item):
        """Handle the nuances of the enable type

        :param action:
        :param item:
        :return:
        """
        action['type'] = 'enable'
        if 'asm_policy' not in item:
            raise F5ModuleError(
                "An 'asm_policy' must be specified when the 'enable' type is used."
            )
        action.update(dict(
            policy=fq_name(self.partition, item['asm_policy']),
            asm=True
        ))


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


class ReportableChanges(Changes):
    returnables = [
        'description', 'actions', 'conditions'
    ]

    @property
    def actions(self):
        result = []
        if self._values['actions'] is None:
            return [dict(type='ignore')]
        for item in self._values['actions']:
            action = dict()
            if 'forward' in item:
                action.update(item)
                action['type'] = 'forward'
                del action['forward']
            elif 'enable' in item:
                action.update(item)
                action['type'] = 'enable'
                del action['enable']
            result.append(action)
        result = sorted(result, key=lambda x: x['name'])
        return result

    @property
    def conditions(self):
        result = []
        if self._values['conditions'] is None:
            return [dict(type='all_traffic')]
        for item in self._values['conditions']:
            action = dict()
            if 'httpUri' in item:
                action.update(item)
                action['type'] = 'http_uri'
                del action['httpUri']
            result.append(action)
        # Names contains the index in which the rule is at.
        result = sorted(result, key=lambda x: x['name'])
        return result


class UsableChanges(Changes):
    @property
    def actions(self):
        if self._values['actions'] is None:
            return None
        result = []
        for action in self._values['actions']:
            if 'type' not in action:
                continue
            if action['type'] == 'forward':
                action['forward'] = True
                del action['type']
            elif action['type'] == 'enable':
                action['enable'] = True
                del action['type']
            elif action['type'] == 'ignore':
                result = []
                break
            result.append(action)
        return result

    @property
    def conditions(self):
        if self._values['conditions'] is None:
            return None
        result = []
        for condition in self._values['conditions']:
            if 'type' not in condition:
                continue
            if condition['type'] == 'http_uri':
                condition['httpUri'] = True
                del condition['type']
            elif condition['type'] == 'all_traffic':
                result = []
                break
            result.append(condition)
        return result


class Difference(object):
    updatables = [
        'actions', 'conditions', 'description'
    ]

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

    def to_tuple(self, items):
        result = []
        for x in items:
            tmp = [(str(k), str(v)) for k, v in iteritems(x)]
            result += tmp
        return result

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None:
            return None
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def actions(self):
        result = self._diff_complex_items(self.want.actions, self.have.actions)
        if self._conditions_missing_default_rule_for_asm(result):
            raise F5ModuleError(
                "The 'all_traffic' condition is required when using an ASM policy in a rule's 'enable' action."
            )
        return result

    @property
    def conditions(self):
        result = self._diff_complex_items(self.want.conditions, self.have.conditions)
        return result

    def _conditions_missing_default_rule_for_asm(self, want_actions):
        if want_actions is None:
            actions = self.have.actions
        else:
            actions = want_actions
        if actions is None:
            return False
        if any(x for x in actions if x['type'] == 'enable'):
            conditions = self._diff_complex_items(self.want.conditions, self.have.conditions)
            if conditions is None:
                return False
            if any(y for y in conditions if y['type'] != 'all_traffic'):
                return True
        return False


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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
        args = dict(
            name=self.want.policy,
            partition=self.want.partition,
        )
        if self.draft_exists():
            args['subPath'] = 'Drafts'

        policy = self.client.api.tm.ltm.policys.policy.load(**args)
        result = policy.rules_s.rules.exists(
            name=self.want.name
        )
        return result

    def draft_exists(self):
        params = dict(
            name=self.want.policy,
            partition=self.want.partition,
            subPath='Drafts'
        )
        result = self.client.api.tm.ltm.policys.policy.exists(**params)
        return result

    def _create_existing_policy_draft_on_device(self):
        params = dict(
            name=self.want.policy,
            partition=self.want.partition,
        )
        resource = self.client.api.tm.ltm.policys.policy.load(**params)
        resource.draft()
        return True

    def publish_on_device(self):
        resource = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.policy,
            partition=self.want.partition,
            subPath='Drafts'
        )
        resource.publish()
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        if self.draft_exists():
            redraft = True
        else:
            redraft = False
            self._create_existing_policy_draft_on_device()
        self.update_on_device()
        if redraft is False:
            self.publish_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        if self.draft_exists():
            redraft = True
        else:
            redraft = False
            self._create_existing_policy_draft_on_device()
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        if redraft is False:
            self.publish_on_device()
        return True

    def create(self):
        self.should_update()
        if self.module.check_mode:
            return True
        if self.draft_exists():
            redraft = True
        else:
            redraft = False
            self._create_existing_policy_draft_on_device()
        self.create_on_device()
        if redraft is False:
            self.publish_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        policy = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.policy,
            partition=self.want.partition,
            subPath='Drafts'
        )
        policy.rules_s.rules.create(
            name=self.want.name,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        policy = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.policy,
            partition=self.want.partition,
            subPath='Drafts'
        )
        resource = policy.rules_s.rules.load(
            name=self.want.name
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        policy = self.client.api.tm.ltm.policys.policy.load(
            name=self.want.policy,
            partition=self.want.partition,
            subPath='Drafts'
        )
        resource = policy.rules_s.rules.load(
            name=self.want.name
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        args = dict(
            name=self.want.policy,
            partition=self.want.partition,
        )
        if self.draft_exists():
            args['subPath'] = 'Drafts'
        policy = self.client.api.tm.ltm.policys.policy.load(**args)
        resource = policy.rules_s.rules.load(
            name=self.want.name,
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return ApiParameters(params=resource.attrs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            description=dict(),
            actions=dict(
                type='list',
                elements='dict',
                options=dict(
                    type=dict(
                        choices=[
                            'forward',
                            'enable',
                            'ignore'
                        ],
                        required=True
                    ),
                    pool=dict(),
                    asm_policy=dict(),
                    virtual=dict()
                ),
                mutually_exclusive=[
                    ['pool', 'asm_policy', 'virtual']
                ]
            ),
            conditions=dict(
                type='list',
                options=dict(
                    type=dict(
                        choices=[
                            'http_uri',
                            'all_traffic'
                        ],
                        required=True
                    ),
                    path_begins_with_any=dict()
                ),
            ),
            name=dict(required=True),
            policy=dict(required=True),
            state=dict(
                default='present',
                choices=['absent', 'present']
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
