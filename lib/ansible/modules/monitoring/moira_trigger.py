#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, SKB Kontur.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

'''Ansible module to create, update and delete Moira triggers

'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: moira_trigger
short_description: Working with large number of triggers in Moira.
description:
    - Create new triggers.
    - Edit existing triggers parameters.
    - Delete triggers.
version_added: '2.4'
author: 'SKB Kontur'
requirements:
    - 'python >= 2.7'
    - 'moira-client >= 0.4'
options:
  api_url:
    description:
      - Url of Moira API.
    required: True
  login:
    description:
      - Auth Login.
    required: False
    default: None
  auth_user:
    description:
      - Auth User.
    required: False
    default: None
  auth_pass:
    description:
      - Auth Password.
    required: False
    default: None
  state:
    description:
      - Desired state of a trigger.
      - Use state 'present' to create and edit existing triggers.
      - Use state 'absent' to delete triggers.
    required: True
    choices: ['present', 'absent']
  name:
    description:
      - Trigger name.
    required: True
  desc:
    description:
      - Trigger description.
    required: False
    default: ''
  ttl:
    description:
      - Time To Live.
    required: False
    default: '600'
  ttl_state:
    description:
      - Trigger state at the expiration of TTL.
    required: False
    default: 'NODATA'
    choices: ['NODATA', 'ERROR', 'WARN', 'OK']
  expression:
    description:
      - Python expression.
    required: False
    default: ''
  disabled_days:
    description:
      - Days for trigger to be in silent mode.
    required: False
    default: {}
  targets:
    description:
      - List of trigger targets.
    required: True
  tags:
    description:
      - List of trigger tags.
    required: False
    default: []
  warn_value:
    description:
      - Value to set WARN status.
    required: False
    default: None
  error_value:
    description:
      - Value to set ERROR status.
    required: False
    default: None
notes:
    - More details at https://github.com/moira-alert/ansible-module.
'''

EXAMPLES = '''
# Trigger creation example.
- name: MoiraAnsible
  moira_trigger:
     api_url: http://localhost/api/
     state: present
     name: '{{ item.name }}'
     desc: trigger test description
     warn_value: 300
     error_value: 600
     ttl_state: ERROR
     tags:
       - first_tag
       - second_tag
     targets: '{{ item.targets }}'
     disabled_days:
       ? Mon
       ? Wed
  with_items:
    - name: test1
      targets:
        - test1.rps
        - test2.rps
    - name: test2
      targets:
        - test3.rps
        - test4.rps
'''

RETURN = '''
success:
  description: Dictionary with current trigger state and id
  returned: success
  type: dict
  sample: {
    'test2': {
      'new trigger created': 'faf5cc42-6199-4f98-ab1f-5047409e0d2f'
    }
  }
'''

try:
    from moira_client import Moira
    HAS_MOIRA_CLIENT = True
except ImportError:
    HAS_MOIRA_CLIENT = False

from ansible.module_utils.basic import AnsibleModule


class MoiraAnsible(object):

    '''Create, edit and delete Moira triggers.

    Attributes:
        moira_api (class): moira api client.
        changed (bool): actual trigger state.
        dry_run (bool): enables check mode.
        failed (dict): error message (if occurred).
        success (dict): trigger state and id.
        warnings (list): module warnings.

    '''

    def __init__(self,
                 moira_api,
                 changed=False,
                 dry_run=False,
                 failed=None,
                 success=None,
                 warnings=None):

        self.moira_api = moira_api
        self.changed = changed
        self.dry_run = dry_run
        failed = {}
        self.failed = failed
        success = {}
        self.success = success
        warnings = []
        self.warnings = warnings

    def exception_handler(self, occurred, component,
                          desc='API Request Failed',
                          level='error'):

        '''Handling occurred exceptions.

        Args:
            occurred (class): exception.
            component (str): component name.
            desc (str): description.
            level (str): level of importance ('warn' or 'error').

        '''

        if level == 'error':

            exception_body = {
                'error': occurred.__class__.__name__,
                'details': str(occurred)}

            if desc not in self.failed:
                self.failed[desc] = {
                    component: exception_body}

            else:
                self.failed[desc].update({
                    component: exception_body})

        elif level == 'warn':

            exception_body = (
                component + ' warning: ' + desc +
                ' Reason: ' + occurred.__class__.__name__)

            self.warnings.append(
                exception_body)

    def api_check(self):

        '''Moira API availability check.

        Returns:
            True if no exceptions occurred, False otherwise.

        '''

        desc = 'API Unavailable'
        components = 'pattern', 'tag', 'trigger'

        for component in components:

            try:
                self.moira_api.trigger.trigger_client.get(component)
            except Exception as api_check_exception:
                self.exception_handler(
                    occurred=api_check_exception,
                    component=component,
                    desc=desc)

        return bool(desc not in self.failed)

    def tag_cleanup(self):

        '''Remove unused tags.

        '''

        unused = set()

        not_removed = 'Unable to remove unused tags. ' \
                      'Tags can be removed on the next module execution.'

        try:
            for tag in self.moira_api.tag.stats():
                if not tag.triggers:
                    unused.add(self.moira_api.tag.delete(tag.name))
            assert False not in unused
        except Exception as tag_cleanup_exception:
            self.exception_handler(
                occurred=tag_cleanup_exception,
                component='Tag Cleanup (tag.stats)',
                desc=not_removed,
                level='warn')

    def get_trigger_id(self, trigger_name):

        '''Get trigger id by trigger name.

        Args:
            trigger_name (str): name of a trigger.

        Returns:
            Trigger id if found, None otherwise.

        '''

        try:
            all_triggers = self.moira_api.trigger.fetch_all()
        except Exception as get_trigger_id_exception:
            self.exception_handler(
                occurred=get_trigger_id_exception,
                component='Get Trigger ID (trigger.fetch_all)')
            return

        for moira_trigger in all_triggers:
            if moira_trigger.name == trigger_name:
                return moira_trigger.id

    def trigger_update_check(self, moira_trigger, trigger):

        '''Check to make sure the trigger was updated.

        Args:
            moira_trigger (class): existing Moira trigger.
            trigger (dict): desired params for existing trigger.

        '''

        not_updated = {}

        for parameter in trigger:
            if not moira_trigger.__dict__[parameter] == trigger[parameter]:
                not_updated.update({
                    parameter: {
                        'desired': trigger[parameter],
                        'actual': moira_trigger.__dict__[parameter]}})

        if not_updated:
            self.failed['failed_to_update_trigger'] = {
                'trigger': trigger['name'],
                'parameters': not_updated}
        else:
            self.changed = True

    def trigger_update(self, moira_trigger, trigger):

        '''Updates parameters of existing trigger.

        Args:
            moira_trigger (class): existing Moira trigger.
            trigger (dict): desired params for existing trigger.

        '''

        trigger_name = trigger['name']

        for parameter in trigger:
            if not moira_trigger.__dict__[parameter] == trigger[parameter]:
                moira_trigger.__dict__[parameter] = trigger[parameter]

        if not self.dry_run:

            try:
                moira_trigger.update()
            except Exception as trigger_update_exception:
                self.exception_handler(
                    occurred=trigger_update_exception,
                    component='Trigger Update (trigger.update)')

            self.trigger_update_check(moira_trigger, trigger)

        else:

            self.changed = True

        if trigger_name not in self.success:

            self.success[trigger_name] = {
                'trigger changed': moira_trigger.id}

    def trigger_remove(self, trigger_name, trigger_id):

        '''Remove trigger.

        Args:
            trigger_name (str): trigger name.
            trigger_id (str): trigger id.

        '''

        if trigger_id is None:

            self.success.update({
                trigger_name: 'no id found for trigger'})

        else:

            if not self.dry_run:

                try:
                    self.moira_api.trigger.delete(trigger_id)
                except Exception as trigger_remove_exception:
                    self.exception_handler(
                        occurred=trigger_remove_exception,
                        component='Remove Trigger (trigger.delete)')
                    return

            self.changed = True
            self.success[trigger_name] = {
                'trigger removed': trigger_id}

    def trigger_edit(self, trigger, trigger_id):

        '''Create new or edit existing trigger.

        Args:
            trigger (dict): desired trigger params.
            trigger_id (str): trigger id.

        '''

        if trigger_id is not None:

            try:
                moira_trigger = self.moira_api.trigger.fetch_by_id(trigger_id)
            except Exception as trigger_edit_exception:
                self.exception_handler(
                    occurred=trigger_edit_exception,
                    component='Trigger Edit (trigger.fetch_by_id)')
                return

        else:

            moira_trigger = self.moira_api.trigger.create(**trigger)

            if not self.dry_run:

                try:
                    moira_trigger.save()
                except Exception as trigger_save_exception:
                    self.exception_handler(
                        occurred=trigger_save_exception,
                        component='Trigger Edit (trigger.save)')
                    return

                moira_trigger_id = moira_trigger.id

            else:

                moira_trigger_id = 'gh0st'

            self.changed = True
            self.success[trigger['name']] = {
                'new trigger created': moira_trigger_id}

        self.trigger_update(moira_trigger, trigger)

    def trigger_customize(self, trigger, state):

        '''General function to work with triggers.

        Args:
            trigger (dict): desired trigger params.
            state (str): desired trigger state.

        '''

        current_id = self.get_trigger_id(trigger['name'])

        if state == 'absent':
            self.trigger_remove(
                trigger_name=trigger['name'],
                trigger_id=current_id)

        elif state == 'present':
            self.trigger_edit(
                trigger=trigger,
                trigger_id=current_id)


def main():

    '''Interact with Moira API via Ansible.

    '''

    fields = {
        'api_url': {
            'type': 'str',
            'required': True},
        'login': {
            'type': 'str',
            'required': False},
        'auth_user': {
            'type': 'str',
            'required': False},
        'auth_pass': {
            'type': 'str',
            'required': False,
            'no_log': True},
        'state': {
            'type': 'str',
            'required': True,
            'choices': ['present', 'absent']},
        'name': {
            'type': 'str',
            'required': True},
        'desc': {
            'type': 'str',
            'required': False,
            'default': ''},
        'ttl': {
            'type': 'str',
            'required': False},
        'ttl_state': {
            'type': 'str',
            'required': False,
            'choices': ['NODATA', 'ERROR', 'WARN', 'OK']},
        'expression': {
            'type': 'str',
            'required': False,
            'default': ''},
        'disabled_days': {
            'type': 'dict',
            'required': False,
            'default': {}},
        'targets': {
            'type': 'list',
            'required': True},
        'tags': {
            'type': 'list',
            'required': False,
            'default': []},
        'warn_value': {
            'type': 'int',
            'required': False},
        'error_value': {
            'type': 'int',
            'required': False}}

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=True)

    missing_moira_client = 'Unable to import required module. ' \
                           'Make sure you have moira-client installed: ' \
                           'pip install moira-client'

    api = {}
    api_parameters = 'api_url', 'login', 'auth_user', 'auth_pass'

    for parameter in api_parameters:
        if module.params[parameter]:
            api.update({parameter: module.params[parameter]})

    trigger = {}
    trigger_parameters_static = 'name', 'ttl', 'ttl_state', \
                                'targets', 'warn_value', 'error_value'

    trigger_parameters_dynamic = 'expression', 'disabled_days', \
                                 'desc', 'tags'

    for parameter in trigger_parameters_static:
        if module.params[parameter]:
            trigger.update({parameter: module.params[parameter]})

    for parameter in trigger_parameters_dynamic:
        trigger.update({parameter: module.params[parameter]})

    if not HAS_MOIRA_CLIENT:
        module.fail_json(msg=missing_moira_client)

    moira_api = Moira(**api)
    moira_ansible = MoiraAnsible(
        moira_api=moira_api,
        dry_run=module.check_mode)

    if not moira_ansible.api_check():
        module.fail_json(msg=moira_ansible.failed)

    moira_ansible.trigger_customize(
        trigger=trigger,
        state=module.params['state'])

    if not module.check_mode:
        moira_ansible.tag_cleanup()

    if not moira_ansible.failed:
        module.exit_json(
            changed=moira_ansible.changed,
            result=moira_ansible.success,
            warnings=moira_ansible.warnings)
    else:
        module.fail_json(
            msg=moira_ansible.failed,
            warnings=moira_ansible.warnings)


if __name__ == '__main__':
    main()
