#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Kenneth D. Evensen <kdevensen@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
module: pamd
author:
    - Kenneth D. Evensen (@kevensen)
short_description: Manage PAM Modules
description:
  - Edit PAM service's type, control, module path and module arguments.
  - In order for a PAM rule to be modified, the type, control and
    module_path must match an existing rule.  See man(5) pam.d for details.
version_added: "2.3"
options:
  name:
    description:
      - The name generally refers to the PAM service file to
        change, for example system-auth.
    type: str
    required: true
  type:
    description:
      - The type of the PAM rule being modified.
      - The C(type), C(control) and C(module_path) all must match a rule to be modified.
    type: str
    required: true
    choices: [ account, -account, auth, -auth, password, -password, session, -session ]
  control:
    description:
      - The control of the PAM rule being modified.
      - This may be a complicated control with brackets. If this is the case, be
        sure to put "[bracketed controls]" in quotes.
      - The C(type), C(control) and C(module_path) all must match a rule to be modified.
    type: str
    required: true
  module_path:
    description:
      - The module path of the PAM rule being modified.
      - The C(type), C(control) and C(module_path) all must match a rule to be modified.
    type: str
    required: true
  new_type:
    description:
    - The new type to assign to the new rule.
    type: str
    choices: [ account, -account, auth, -auth, password, -password, session, -session ]
  new_control:
    description:
    - The new control to assign to the new rule.
    type: str
  new_module_path:
    description:
    - The new module path to be assigned to the new rule.
    type: str
  module_arguments:
    description:
    - When state is C(updated), the module_arguments will replace existing module_arguments.
    - When state is C(args_absent) args matching those listed in module_arguments will be removed.
    - When state is C(args_present) any args listed in module_arguments are added if
      missing from the existing rule.
    - Furthermore, if the module argument takes a value denoted by C(=),
      the value will be changed to that specified in module_arguments.
    type: list
  state:
    description:
    - The default of C(updated) will modify an existing rule if type,
      control and module_path all match an existing rule.
    - With C(before), the new rule will be inserted before a rule matching type,
      control and module_path.
    - Similarly, with C(after), the new rule will be inserted after an existing rulematching type,
      control and module_path.
    - With either C(before) or C(after) new_type, new_control, and new_module_path must all be specified.
    - If state is C(args_absent) or C(args_present), new_type, new_control, and new_module_path will be ignored.
    - State C(absent) will remove the rule.  The 'absent' state was added in Ansible 2.4.
    type: str
    choices: [ absent, before, after, args_absent, args_present, updated ]
    default: updated
  path:
    description:
    - This is the path to the PAM service files.
    type: path
    default: /etc/pam.d
  backup:
     description:
       - Create a backup file including the timestamp information so you can
         get the original file back if you somehow clobbered it incorrectly.
     type: bool
     default: no
     version_added: '2.6'
'''

EXAMPLES = r'''
- name: Update pamd rule's control in /etc/pam.d/system-auth
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    new_control: sufficient

- name: Update pamd rule's complex control in /etc/pam.d/system-auth
  pamd:
    name: system-auth
    type: session
    control: '[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    new_control: '[success=2 default=ignore]'

- name: Insert a new rule before an existing rule
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    new_type: auth
    new_control: sufficient
    new_module_path: pam_faillock.so
    state: before

- name: Insert a new rule pam_wheel.so with argument 'use_uid' after an \
        existing rule pam_rootok.so
  pamd:
    name: su
    type: auth
    control: sufficient
    module_path: pam_rootok.so
    new_type: auth
    new_control: required
    new_module_path: pam_wheel.so
    module_arguments: 'use_uid'
    state: after

- name: Remove module arguments from an existing rule
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    module_arguments: ''
    state: updated

- name: Replace all module arguments in an existing rule
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    module_arguments: 'preauth
        silent
        deny=3
        unlock_time=604800
        fail_interval=900'
    state: updated

- name: Remove specific arguments from a rule
  pamd:
    name: system-auth
    type: session
    control: '[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    module_arguments: crond,quiet
    state: args_absent

- name: Ensure specific arguments are present in a rule
  pamd:
    name: system-auth
    type: session
    control: '[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    module_arguments: crond,quiet
    state: args_present

- name: Ensure specific arguments are present in a rule (alternative)
  pamd:
    name: system-auth
    type: session
    control: '[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    module_arguments:
    - crond
    - quiet
    state: args_present

- name: Module arguments requiring commas must be listed as a Yaml list
  pamd:
    name: special-module
    type: account
    control: required
    module_path: pam_access.so
    module_arguments:
    - listsep=,
    state: args_present

- name: Update specific argument value in a rule
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    module_arguments: 'fail_interval=300'
    state: args_present

- name: Add pam common-auth rule for duo
  pamd:
    name: common-auth
    new_type: auth
    new_control: '[success=1 default=ignore]'
    new_module_path: '/lib64/security/pam_duo.so'
    state: after
    type: auth
    module_path: pam_sss.so
    control: 'requisite'
'''

RETURN = r'''
change_count:
    description: How many rules were changed.
    type: int
    sample: 1
    returned: success
    version_added: 2.4
new_rule:
    description: The changes to the rule.  This was available in Ansible 2.4 and Ansible 2.5.  It was removed in Ansible 2.6.
    type: str
    sample: None      None None sha512 shadow try_first_pass use_authtok
    returned: success
    version_added: 2.4
updated_rule_(n):
    description: The rule(s) that was/were changed.  This is only available in
      Ansible 2.4 and was removed in Ansible 2.5.
    type: str
    sample:
    - password      sufficient  pam_unix.so sha512 shadow try_first_pass
      use_authtok
    returned: success
    version_added: 2.4
action:
    description:
    - "That action that was taken and is one of: update_rule,
      insert_before_rule, insert_after_rule, args_present, args_absent,
      absent. This was available in Ansible 2.4 and removed in Ansible 2.8"
    returned: always
    type: str
    sample: "update_rule"
    version_added: 2.4
dest:
    description:
    - "Path to pam.d service that was changed.  This is only available in
      Ansible 2.3 and was removed in Ansible 2.4."
    returned: success
    type: str
    sample: "/etc/pam.d/system-auth"
backupdest:
    description:
    - "The file name of the backup file, if created."
    returned: success
    type: str
    version_added: 2.6
...
'''


from ansible.module_utils.basic import AnsibleModule
import os
import re
from tempfile import NamedTemporaryFile
from datetime import datetime


RULE_REGEX = re.compile(r"""(?P<rule_type>-?(?:auth|account|session|password))\s+
                        (?P<control>\[.*\]|\S*)\s+
                        (?P<path>\S*)\s*
                        (?P<args>.*)\s*""", re.X)

RULE_ARG_REGEX = re.compile(r"""(\[.*\]|\S*)""")

VALID_TYPES = ['account', '-account', 'auth', '-auth', 'password', '-password', 'session', '-session']


class PamdLine(object):

    def __init__(self, line):
        self.line = line
        self.prev = None
        self.next = None

    @property
    def is_valid(self):
        if self.line == '':
            return True
        return False

    def validate(self):
        if not self.is_valid:
            return False, "Rule is not valid " + self.line
        return True, "Rule is valid " + self.line

    # Method to check if a rule matches the type, control and path.
    def matches(self, rule_type, rule_control, rule_path, rule_args=None):
        return False

    def __str__(self):
        return str(self.line)


class PamdComment(PamdLine):

    def __init__(self, line):
        super(PamdComment, self).__init__(line)

    @property
    def is_valid(self):
        if self.line.startswith('#'):
            return True
        return False


class PamdInclude(PamdLine):
    def __init__(self, line):
        super(PamdInclude, self).__init__(line)

    @property
    def is_valid(self):
        if self.line.startswith('@include'):
            return True
        return False


class PamdRule(PamdLine):

    valid_simple_controls = ['required', 'requisite', 'sufficient', 'optional', 'include', 'substack', 'definitive']
    valid_control_values = ['success', 'open_err', 'symbol_err', 'service_err', 'system_err', 'buf_err',
                            'perm_denied', 'auth_err', 'cred_insufficient', 'authinfo_unavail', 'user_unknown',
                            'maxtries', 'new_authtok_reqd', 'acct_expired', 'session_err', 'cred_unavail',
                            'cred_expired', 'cred_err', 'no_module_data', 'conv_err', 'authtok_err',
                            'authtok_recover_err', 'authtok_lock_busy', 'authtok_disable_aging', 'try_again',
                            'ignore', 'abort', 'authtok_expired', 'module_unknown', 'bad_item', 'conv_again',
                            'incomplete', 'default']
    valid_control_actions = ['ignore', 'bad', 'die', 'ok', 'done', 'reset']

    def __init__(self, rule_type, rule_control, rule_path, rule_args=None):
        self._control = None
        self._args = None
        self.rule_type = rule_type
        self.rule_control = rule_control

        self.rule_path = rule_path
        self.rule_args = rule_args

    # Method to check if a rule matches the type, control and path.
    def matches(self, rule_type, rule_control, rule_path, rule_args=None):
        if (rule_type == self.rule_type and
                rule_control == self.rule_control and
                rule_path == self.rule_path):
            return True
        return False

    @classmethod
    def rule_from_string(cls, line):
        rule_match = RULE_REGEX.search(line)
        rule_args = parse_module_arguments(rule_match.group('args'))
        return cls(rule_match.group('rule_type'), rule_match.group('control'), rule_match.group('path'), rule_args)

    def __str__(self):
        if self.rule_args:
            return '{0: <11}{1} {2} {3}'.format(self.rule_type, self.rule_control, self.rule_path, ' '.join(self.rule_args))
        return '{0: <11}{1} {2}'.format(self.rule_type, self.rule_control, self.rule_path)

    @property
    def rule_control(self):
        if isinstance(self._control, list):
            return '[' + ' '.join(self._control) + ']'
        return self._control

    @rule_control.setter
    def rule_control(self, control):
        if control.startswith('['):
            control = control.replace(' = ', '=').replace('[', '').replace(']', '')
            self._control = control.split(' ')
        else:
            self._control = control

    @property
    def rule_args(self):
        if not self._args:
            return []
        return self._args

    @rule_args.setter
    def rule_args(self, args):
        self._args = parse_module_arguments(args)

    @property
    def line(self):
        return str(self)

    @classmethod
    def is_action_unsigned_int(cls, string_num):
        number = 0
        try:
            number = int(string_num)
        except ValueError:
            return False

        if number >= 0:
            return True
        return False

    @property
    def is_valid(self):
        return self.validate()[0]

    def validate(self):
        # Validate the rule type
        if self.rule_type not in VALID_TYPES:
            return False, "Rule type, " + self.rule_type + ", is not valid in rule " + self.line
        # Validate the rule control
        if isinstance(self._control, str) and self.rule_control not in PamdRule.valid_simple_controls:
            return False, "Rule control, " + self.rule_control + ", is not valid in rule " + self.line
        elif isinstance(self._control, list):
            for control in self._control:
                value, action = control.split("=")
                if value not in PamdRule.valid_control_values:
                    return False, "Rule control value, " + value + ", is not valid in rule " + self.line
                if action not in PamdRule.valid_control_actions and not PamdRule.is_action_unsigned_int(action):
                    return False, "Rule control action, " + action + ", is not valid in rule " + self.line

        # TODO: Validate path

        return True, "Rule is valid " + self.line


# PamdService encapsulates an entire service and contains one or more rules.  It seems the best way is to do this
# as a doubly linked list.
class PamdService(object):

    def __init__(self, content):
        self._head = None
        self._tail = None
        for line in content.splitlines():
            if line.lstrip().startswith('#'):
                pamd_line = PamdComment(line)
            elif line.lstrip().startswith('@include'):
                pamd_line = PamdInclude(line)
            elif line == '':
                pamd_line = PamdLine(line)
            else:
                pamd_line = PamdRule.rule_from_string(line)

            self.append(pamd_line)

    def append(self, pamd_line):
        if self._head is None:
            self._head = self._tail = pamd_line
        else:
            pamd_line.prev = self._tail
            pamd_line.next = None
            self._tail.next = pamd_line
            self._tail = pamd_line

    def remove(self, rule_type, rule_control, rule_path):
        current_line = self._head
        changed = 0

        while current_line is not None:
            if current_line.matches(rule_type, rule_control, rule_path):
                if current_line.prev is not None:
                    current_line.prev.next = current_line.next
                    current_line.next.prev = current_line.prev
                else:
                    self._head = current_line.next
                    current_line.next.prev = None
                changed += 1

            current_line = current_line.next
        return changed

    def get(self, rule_type, rule_control, rule_path):
        lines = []
        current_line = self._head
        while current_line is not None:

            if isinstance(current_line, PamdRule) and current_line.matches(rule_type, rule_control, rule_path):
                lines.append(current_line)

            current_line = current_line.next

        return lines

    def has_rule(self, rule_type, rule_control, rule_path):
        if self.get(rule_type, rule_control, rule_path):
            return True
        return False

    def update_rule(self, rule_type, rule_control, rule_path,
                    new_type=None, new_control=None, new_path=None, new_args=None):
        # Get a list of rules we want to change
        rules_to_find = self.get(rule_type, rule_control, rule_path)

        new_args = parse_module_arguments(new_args)

        changes = 0
        for current_rule in rules_to_find:
            rule_changed = False
            if new_type:
                if(current_rule.rule_type != new_type):
                    rule_changed = True
                    current_rule.rule_type = new_type
            if new_control:
                if(current_rule.rule_control != new_control):
                    rule_changed = True
                    current_rule.rule_control = new_control
            if new_path:
                if(current_rule.rule_path != new_path):
                    rule_changed = True
                    current_rule.rule_path = new_path
            if new_args:
                if(current_rule.rule_args != new_args):
                    rule_changed = True
                    current_rule.rule_args = new_args

            if rule_changed:
                changes += 1

        return changes

    def insert_before(self, rule_type, rule_control, rule_path,
                      new_type=None, new_control=None, new_path=None, new_args=None):
        # Get a list of rules we want to change
        rules_to_find = self.get(rule_type, rule_control, rule_path)
        changes = 0
        # There are two cases to consider.
        # 1. The new rule doesn't exist before the existing rule
        # 2. The new rule exists

        for current_rule in rules_to_find:
            # Create a new rule
            new_rule = PamdRule(new_type, new_control, new_path, new_args)
            # First we'll get the previous rule.
            previous_rule = current_rule.prev

            # Next we may have to loop backwards if the previous line is a comment.  If it
            # is, we'll get the previous "rule's" previous.
            while previous_rule is not None and isinstance(previous_rule, PamdComment):
                previous_rule = previous_rule.prev
            # Next we'll see if the previous rule matches what we are trying to insert.
            if previous_rule is not None and not previous_rule.matches(new_type, new_control, new_path):
                # First set the original previous rule's next to the new_rule
                previous_rule.next = new_rule
                # Second, set the new_rule's previous to the original previous
                new_rule.prev = previous_rule
                # Third, set the new rule's next to the current rule
                new_rule.next = current_rule
                # Fourth, set the current rule's previous to the new_rule
                current_rule.prev = new_rule

                changes += 1

            # Handle the case where it is the first rule in the list.
            elif previous_rule is None:
                # This is the case where the current rule is not only the first rule
                # but the first line as well.  So we set the head to the new rule
                if current_rule.prev is None:
                    self._head = new_rule
                # This case would occur if the previous line was a comment.
                else:
                    current_rule.prev.next = new_rule
                new_rule.prev = current_rule.prev
                new_rule.next = current_rule
                current_rule.prev = new_rule
                changes += 1

        return changes

    def insert_after(self, rule_type, rule_control, rule_path,
                     new_type=None, new_control=None, new_path=None, new_args=None):
        # Get a list of rules we want to change
        rules_to_find = self.get(rule_type, rule_control, rule_path)
        changes = 0
        # There are two cases to consider.
        # 1. The new rule doesn't exist after the existing rule
        # 2. The new rule exists
        for current_rule in rules_to_find:
            # First we'll get the next rule.
            next_rule = current_rule.next
            # Next we may have to loop forwards if the next line is a comment.  If it
            # is, we'll get the next "rule's" next.
            while next_rule is not None and isinstance(next_rule, PamdComment):
                next_rule = next_rule.next

            # First we create a new rule
            new_rule = PamdRule(new_type, new_control, new_path, new_args)
            if next_rule is not None and not next_rule.matches(new_type, new_control, new_path):
                # If the previous rule doesn't match we'll insert our new rule.

                # Second set the original next rule's previuous to the new_rule
                next_rule.prev = new_rule
                # Third, set the new_rule's next to the original next rule
                new_rule.next = next_rule
                # Fourth, set the new rule's previous to the current rule
                new_rule.prev = current_rule
                # Fifth, set the current rule's next to the new_rule
                current_rule.next = new_rule

                changes += 1

            # This is the case where the current_rule is the last in the list
            elif next_rule is None:
                new_rule.prev = self._tail
                new_rule.next = None
                self._tail.next = new_rule
                self._tail = new_rule

                current_rule.next = new_rule
                changes += 1

        return changes

    def add_module_arguments(self, rule_type, rule_control, rule_path, args_to_add):
        # Get a list of rules we want to change
        rules_to_find = self.get(rule_type, rule_control, rule_path)

        args_to_add = parse_module_arguments(args_to_add)

        changes = 0

        for current_rule in rules_to_find:
            rule_changed = False

            # create some structures to evaluate the situation
            simple_new_args = set()
            key_value_new_args = dict()

            for arg in args_to_add:
                if arg.startswith("["):
                    continue
                elif "=" in arg:
                    key, value = arg.split("=")
                    key_value_new_args[key] = value
                else:
                    simple_new_args.add(arg)

            key_value_new_args_set = set(key_value_new_args)

            simple_current_args = set()
            key_value_current_args = dict()

            for arg in current_rule.rule_args:
                if arg.startswith("["):
                    continue
                elif "=" in arg:
                    key, value = arg.split("=")
                    key_value_current_args[key] = value
                else:
                    simple_current_args.add(arg)

            key_value_current_args_set = set(key_value_current_args)

            new_args_to_add = list()

            # Handle new simple arguments
            if simple_new_args.difference(simple_current_args):
                for arg in simple_new_args.difference(simple_current_args):
                    new_args_to_add.append(arg)

            # Handle new key value arguments
            if key_value_new_args_set.difference(key_value_current_args_set):
                for key in key_value_new_args_set.difference(key_value_current_args_set):
                    new_args_to_add.append(key + '=' + key_value_new_args[key])

            if new_args_to_add:
                current_rule.rule_args += new_args_to_add
                rule_changed = True

            # Handle existing key value arguments when value is not equal
            if key_value_new_args_set.intersection(key_value_current_args_set):
                for key in key_value_new_args_set.intersection(key_value_current_args_set):
                    if key_value_current_args[key] != key_value_new_args[key]:
                        arg_index = current_rule.rule_args.index(key + '=' + key_value_current_args[key])
                        current_rule.rule_args[arg_index] = str(key + '=' + key_value_new_args[key])
                        rule_changed = True

            if rule_changed:
                changes += 1

        return changes

    def remove_module_arguments(self, rule_type, rule_control, rule_path, args_to_remove):
        # Get a list of rules we want to change
        rules_to_find = self.get(rule_type, rule_control, rule_path)

        args_to_remove = parse_module_arguments(args_to_remove)

        changes = 0

        for current_rule in rules_to_find:
            if not args_to_remove:
                args_to_remove = []

            # Let's check to see if there are any args to remove by finding the intersection
            # of the rule's current args and the args_to_remove lists
            if not list(set(current_rule.rule_args) & set(args_to_remove)):
                continue

            # There are args to remove, so we create a list of new_args absent the args
            # to remove.
            current_rule.rule_args = [arg for arg in current_rule.rule_args if arg not in args_to_remove]

            changes += 1

        return changes

    def validate(self):
        current_line = self._head

        while current_line is not None:
            if not current_line.validate()[0]:
                return current_line.validate()
            current_line = current_line.next
        return True, "Module is valid"

    def __str__(self):
        lines = []
        current_line = self._head

        while current_line is not None:
            lines.append(str(current_line))
            current_line = current_line.next

        if lines[1].startswith("# Updated by Ansible"):
            lines.pop(1)

        lines.insert(1, "# Updated by Ansible - " + datetime.now().isoformat())

        return '\n'.join(lines) + '\n'


def parse_module_arguments(module_arguments):
    # Return empty list if we have no args to parse
    if not module_arguments:
        return []
    elif isinstance(module_arguments, list) and len(module_arguments) == 1 and not module_arguments[0]:
        return []

    if not isinstance(module_arguments, list):
        module_arguments = [module_arguments]

    parsed_args = list()

    for arg in module_arguments:
        for item in filter(None, RULE_ARG_REGEX.findall(arg)):
            if not item.startswith("["):
                re.sub("\\s*=\\s*", "=", item)
            parsed_args.append(item)

    return parsed_args


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            type=dict(type='str', required=True, choices=VALID_TYPES),
            control=dict(type='str', required=True),
            module_path=dict(type='str', required=True),
            new_type=dict(type='str', choices=VALID_TYPES),
            new_control=dict(type='str'),
            new_module_path=dict(type='str'),
            module_arguments=dict(type='list'),
            state=dict(type='str', default='updated', choices=['absent', 'after', 'args_absent', 'args_present', 'before', 'updated']),
            path=dict(type='path', default='/etc/pam.d'),
            backup=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_if=[
            ("state", "args_present", ["module_arguments"]),
            ("state", "args_absent", ["module_arguments"]),
            ("state", "before", ["new_control"]),
            ("state", "before", ["new_type"]),
            ("state", "before", ["new_module_path"]),
            ("state", "after", ["new_control"]),
            ("state", "after", ["new_type"]),
            ("state", "after", ["new_module_path"]),

        ],
    )
    content = str()
    fname = os.path.join(module.params["path"], module.params["name"])

    # Open the file and read the content or fail
    try:
        with open(fname, 'r') as service_file_obj:
            content = service_file_obj.read()
    except IOError as e:
        # If unable to read the file, fail out
        module.fail_json(msg='Unable to open/read PAM module \
                            file %s with error %s.' %
                         (fname, str(e)))

    # Assuming we didnt fail, create the service
    service = PamdService(content)
    # Set the action
    action = module.params['state']

    changes = 0

    # Take action
    if action == 'updated':
        changes = service.update_rule(module.params['type'], module.params['control'], module.params['module_path'],
                                      module.params['new_type'], module.params['new_control'], module.params['new_module_path'],
                                      module.params['module_arguments'])
    elif action == 'before':
        changes = service.insert_before(module.params['type'], module.params['control'], module.params['module_path'],
                                        module.params['new_type'], module.params['new_control'], module.params['new_module_path'],
                                        module.params['module_arguments'])
    elif action == 'after':
        changes = service.insert_after(module.params['type'], module.params['control'], module.params['module_path'],
                                       module.params['new_type'], module.params['new_control'], module.params['new_module_path'],
                                       module.params['module_arguments'])
    elif action == 'args_absent':
        changes = service.remove_module_arguments(module.params['type'], module.params['control'], module.params['module_path'],
                                                  module.params['module_arguments'])
    elif action == 'args_present':
        if [arg for arg in parse_module_arguments(module.params['module_arguments']) if arg.startswith("[")]:
            module.fail_json(msg="Unable to process bracketed '[' complex arguments with 'args_present'. Please use 'updated'.")

        changes = service.add_module_arguments(module.params['type'], module.params['control'], module.params['module_path'],
                                               module.params['module_arguments'])
    elif action == 'absent':
        changes = service.remove(module.params['type'], module.params['control'], module.params['module_path'])

    valid, msg = service.validate()

    # If the module is not valid (meaning one of the rules is invalid), we will fail
    if not valid:
        module.fail_json(msg=msg)

    result = dict(
        changed=(changes > 0),
        change_count=changes,
        backupdest='',
    )

    # If not check mode and something changed, backup the original if necessary then write out the file or fail
    if not module.check_mode and result['changed']:
        # First, create a backup if desired.
        if module.params['backup']:
            result['backupdest'] = module.backup_local(fname)
        try:
            temp_file = NamedTemporaryFile(mode='w', dir=module.tmpdir, delete=False)
            with open(temp_file.name, 'w') as fd:
                fd.write(str(service))

        except IOError:
            module.fail_json(msg='Unable to create temporary \
                                    file %s' % temp_file)

        module.atomic_move(temp_file.name, os.path.realpath(fname))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
