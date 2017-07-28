#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Kenneth D. Evensen <kevensen@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: pamd
author:
    - "Kenneth D. Evensen (@kevensen)"
short_description: Manage PAM Modules
description:
  - Edit PAM service's type, control, module path and module arguments.
    In order for a PAM rule to be modified, the type, control and
    module_path must match an existing rule.  See man(5) pam.d for details.
version_added: "2.3"
options:
  name:
    required: true
    description:
      - The name generally refers to the PAM service file to
        change, for example system-auth.
  type:
    required: true
    description:
      - The type of the PAM rule being modified.  The type, control
        and module_path all must match a rule to be modified.
  control:
    required: true
    description:
      - The control of the PAM rule being modified.  This may be a
        complicated control with brackets.  If this is the case, be
        sure to put "[bracketed controls]" in quotes.  The type,
        control and module_path all must match a rule to be modified.
  module_path:
    required: true
    description:
      - The module path of the PAM rule being modified.  The type,
        control and module_path all must match a rule to be modified.
  new_type:
    description:
    - The new type to assign to the new rule.
  new_control:
    description:
    - The new control to assign to the new rule.
  new_module_path:
    description:
    - The new module path to be assigned to the new rule.
  module_arguments:
    description:
    - When state is 'updated', the module_arguments will replace existing
      module_arguments.  When state is 'args_absent' args matching those
      listed in module_arguments will be removed.  When state is
      'args_present' any args listed in module_arguments are added if
      missing from the existing rule.  Furthermore, if the module argument
      takes a value denoted by '=', the value will be changed to that specified
      in module_arguments.
  state:
    default: updated
    choices:
    - updated
    - before
    - after
    - args_present
    - args_absent
    - absent
    description:
    - The default of 'updated' will modify an existing rule if type,
      control and module_path all match an existing rule.  With 'before',
      the new rule will be inserted before a rule matching type, control
      and module_path.  Similarly, with 'after', the new rule will be inserted
      after an existing rule matching type, control and module_path.  With
      either 'before' or 'after' new_type, new_control, and new_module_path
      must all be specified.  If state is 'args_absent' or 'args_present',
      new_type, new_control, and new_module_path will be ignored.  State
      'absent' will remove the rule.  The 'absent' state was added in version
      2.4 and is only available in Ansible versions >= 2.4.
  path:
    default: /etc/pam.d/
    description:
    - This is the path to the PAM service files
"""

EXAMPLES = """
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
    type: session control='[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    module_arguments: 'crond quiet'
    state: args_absent

- name: Ensure specific arguments are present in a rule
  pamd:
    name: system-auth
    type: session
    control: '[success=1 default=ignore]'
    module_path: pam_succeed_if.so
    module_arguments: 'crond quiet'
    state: args_present

- name: Update specific argument value in a rule
  pamd:
    name: system-auth
    type: auth
    control: required
    module_path: pam_faillock.so
    module_arguments: 'fail_interval=300'
    state: args_present
"""

RETURN = '''
change_count:
    description: How many rules were changed
    type: int
    sample: 1
    returned: success
    version_added: 2.4
new_rule:
    description: The changes to the rule
    type: string
    sample: None      None None sha512 shadow try_first_pass use_authtok
    returned: success
    version_added: 2.4
updated_rule_(n):
    description: The rule(s) that was/were changed
    type: string
    sample:
    - password      sufficient  pam_unix.so sha512 shadow try_first_pass
      use_authtok
    returned: success
    version_added: 2.4
action:
    description:
    - "That action that was taken and is one of: update_rule,
      insert_before_rule, insert_after_rule, args_present, args_absent,
      absent."
    returned: always
    type: string
    sample: "update_rule"
    version_added: 2.4
dest:
    description:
    - "Path to pam.d service that was changed.  This is only available in
      Ansible version 2.3 and was removed in 2.4."
    returned: success
    type: string
    sample: "/etc/pam.d/system-auth"
...
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import os
import re
import time


# The PamdRule class encapsulates a rule in a pam.d service
class PamdRule(object):

    def __init__(self, rule_type,
                 rule_control, rule_module_path,
                 rule_module_args=None):

        self.rule_type = rule_type
        self.rule_control = rule_control
        self.rule_module_path = rule_module_path

        try:
            if (rule_module_args is not None and
                    type(rule_module_args) is list):
                self.rule_module_args = rule_module_args
            elif (rule_module_args is not None and
                    type(rule_module_args) is str):
                self.rule_module_args = rule_module_args.split()
        except AttributeError:
            self.rule_module_args = []

    @classmethod
    def rulefromstring(cls, stringline):
        pattern = None

        rule_type = ''
        rule_control = ''
        rule_module_path = ''
        rule_module_args = ''
        complicated = False

        if '[' in stringline:
            pattern = re.compile(
                r"""([\-A-Za-z0-9_]+)\s*        # Rule Type
                    \[([A-Za-z0-9_=\s]+)\]\s*   # Rule Control
                    ([A-Za-z0-9_\.]+)\s*        # Rule Path
                    ([A-Za-z0-9_=<>\-\s]*)""",  # Rule Args
                re.X)
            complicated = True
        else:
            pattern = re.compile(
                r"""([\-A-Za-z0-9_]+)\s*        # Rule Type
                    ([A-Za-z0-9_]+)\s*          # Rule Control
                    ([A-Za-z0-9_\.]+)\s*        # Rule Path
                    ([A-Za-z0-9_=<>\-\s]*)""",  # Rule Args
                re.X)

        result = pattern.match(stringline)

        rule_type = result.group(1)
        if complicated:
            rule_control = '[' + result.group(2) + ']'
        else:
            rule_control = result.group(2)
        rule_module_path = result.group(3)
        if result.group(4) is not None:
            rule_module_args = result.group(4)

        return cls(rule_type, rule_control, rule_module_path, rule_module_args)

    def get_module_args_as_string(self):
        try:
            if self.rule_module_args is not None:
                return ' '.join(self.rule_module_args)
        except AttributeError:
            pass
        return ''

    def __str__(self):
        return "%-10s\t%s\t%s %s" % (self.rule_type,
                                     self.rule_control,
                                     self.rule_module_path,
                                     self.get_module_args_as_string())


# PamdService encapsulates an entire service and contains one or more rules
class PamdService(object):

    def __init__(self, ansible=None):

        if ansible is not None:
            self.check = ansible.check_mode
        self.check = False
        self.ansible = ansible
        self.preamble = []
        self.rules = []
        self.fname = None
        if ansible is not None:
            self.path = self.ansible.params["path"]
            self.name = self.ansible.params["name"]

    def load_rules_from_file(self):
        self.fname = self.path + "/" + self.name
        stringline = ''
        try:
            for line in open(self.fname, 'r'):
                stringline += line.rstrip()
                stringline += '\n'
            self.load_rules_from_string(stringline)

        except IOError:
            e = get_exception()
            self.ansible.fail_json(msg='Unable to open/read PAM module \
                                   file %s with error %s.  And line %s' %
                                   (self.fname, str(e), stringline))

    def load_rules_from_string(self, stringvalue):
        for line in stringvalue.splitlines():
            stringline = line.rstrip()
            if line.startswith('#') and not line.isspace():
                self.preamble.append(line.rstrip())
            elif (not line.startswith('#') and
                  not line.isspace() and
                  len(line) != 0):
                self.rules.append(PamdRule.rulefromstring(stringline))

    def write(self):
        if self.fname is None:
            self.fname = self.path + "/" + self.name
        # If the file is a symbollic link, we'll write to the source.
        pamd_file = os.path.realpath(self.fname)
        temp_file = "/tmp/" + self.name + "_" + time.strftime("%y%m%d%H%M%S")
        try:
            f = open(temp_file, 'w')
            f.write(str(self))
            f.close()
        except IOError:
            self.ansible.fail_json(msg='Unable to create temporary \
                                   file %s' % self.temp_file)

        self.ansible.atomic_move(temp_file, pamd_file)

    def __str__(self):
        stringvalue = ''
        previous_rule = None
        for amble in self.preamble:
            stringvalue += amble
            stringvalue += '\n'

        for rule in self.rules:
            if (previous_rule is not None and
                    (previous_rule.rule_type.replace('-', '') !=
                     rule.rule_type.replace('-', ''))):
                stringvalue += '\n'
            stringvalue += str(rule).rstrip()
            stringvalue += '\n'
            previous_rule = rule

        if stringvalue.endswith('\n'):
            stringvalue = stringvalue[:-1]

        return stringvalue


def update_rule(service, old_rule, new_rule):

    changed = False
    change_count = 0
    result = {'action': 'update_rule'}

    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):

            if (new_rule.rule_type is not None and
                    new_rule.rule_type != rule.rule_type):
                rule.rule_type = new_rule.rule_type
                changed = True
            if (new_rule.rule_control is not None and
                    new_rule.rule_control != rule.rule_control):
                rule.rule_control = new_rule.rule_control
                changed = True
            if (new_rule.rule_module_path is not None and
                    new_rule.rule_module_path != rule.rule_module_path):
                rule.rule_module_path = new_rule.rule_module_path
                changed = True
            try:
                if (new_rule.rule_module_args is not None and
                        new_rule.get_module_args_as_string() !=
                        rule.get_module_args_as_string()):
                    rule.rule_module_args = new_rule.rule_module_args
                    changed = True
            except AttributeError:
                pass
            if changed:
                result['updated_rule_' + str(change_count)] = str(rule)
                result['new_rule'] = str(new_rule)

                change_count += 1

    result['change_count'] = change_count
    return changed, result


def insert_before_rule(service, old_rule, new_rule):
    index = 0
    change_count = 0
    result = {'action':
              'insert_before_rule'}
    changed = False
    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):
            if index == 0:
                service.rules.insert(0, new_rule)
                changed = True
            elif (new_rule.rule_type != service.rules[index - 1].rule_type or
                    new_rule.rule_control !=
                    service.rules[index - 1].rule_control or
                    new_rule.rule_module_path !=
                    service.rules[index - 1].rule_module_path):
                service.rules.insert(index, new_rule)
                changed = True
            if changed:
                result['new_rule'] = str(new_rule)
                result['before_rule_' + str(change_count)] = str(rule)
                change_count += 1
        index += 1
    result['change_count'] = change_count
    return changed, result


def insert_after_rule(service, old_rule, new_rule):
    index = 0
    change_count = 0
    result = {'action': 'insert_after_rule'}
    changed = False
    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):
            if (new_rule.rule_type != service.rules[index + 1].rule_type or
                    new_rule.rule_control !=
                    service.rules[index + 1].rule_control or
                    new_rule.rule_module_path !=
                    service.rules[index + 1].rule_module_path):
                service.rules.insert(index + 1, new_rule)
                changed = True
            if changed:
                result['new_rule'] = str(new_rule)
                result['after_rule_' + str(change_count)] = str(rule)
                change_count += 1
        index += 1

    result['change_count'] = change_count
    return changed, result


def remove_module_arguments(service, old_rule, module_args):
    result = {'action': 'args_absent'}
    changed = False
    change_count = 0

    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):
            for arg_to_remove in module_args:
                for arg in rule.rule_module_args:
                    if arg == arg_to_remove:
                        rule.rule_module_args.remove(arg)
                        changed = True
                        result['removed_arg_' + str(change_count)] = arg
                        result['from_rule_' + str(change_count)] = str(rule)
                        change_count += 1

    result['change_count'] = change_count
    return changed, result


def add_module_arguments(service, old_rule, module_args):
    result = {'action': 'args_present'}
    changed = False
    change_count = 0

    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):
            for arg_to_add in module_args:
                if "=" in arg_to_add:
                    pre_string = arg_to_add[:arg_to_add.index('=') + 1]
                    indicies = [i for i, arg
                                in enumerate(rule.rule_module_args)
                                if arg.startswith(pre_string)]
                    if len(indicies) == 0:
                        rule.rule_module_args.append(arg_to_add)
                        changed = True
                        result['added_arg_' + str(change_count)] = arg_to_add
                        result['to_rule_' + str(change_count)] = str(rule)
                        change_count += 1
                    else:
                        for i in indicies:
                            if rule.rule_module_args[i] != arg_to_add:
                                rule.rule_module_args[i] = arg_to_add
                                changed = True
                                result['updated_arg_' +
                                       str(change_count)] = arg_to_add
                                result['in_rule_' +
                                       str(change_count)] = str(rule)
                                change_count += 1
                elif arg_to_add not in rule.rule_module_args:
                    rule.rule_module_args.append(arg_to_add)
                    changed = True
                    result['added_arg_' + str(change_count)] = arg_to_add
                    result['to_rule_' + str(change_count)] = str(rule)
                    change_count += 1
    result['change_count'] = change_count
    return changed, result


def remove_rule(service, old_rule):
    result = {'action': 'absent'}
    changed = False
    change_count = 0
    for rule in service.rules:
        if (old_rule.rule_type == rule.rule_type and
                old_rule.rule_control == rule.rule_control and
                old_rule.rule_module_path == rule.rule_module_path):
            service.rules.remove(rule)
            changed = True
    return changed, result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            type=dict(required=True,
                      choices=['account', 'auth',
                               'password', 'session']),
            control=dict(required=True, type='str'),
            module_path=dict(required=True, type='str'),
            new_type=dict(required=False,
                          choices=['account', 'auth',
                                   'password', 'session']),
            new_control=dict(required=False, type='str'),
            new_module_path=dict(required=False, type='str'),
            module_arguments=dict(required=False, type='list'),
            state=dict(required=False, default="updated",
                       choices=['before', 'after', 'updated',
                                'args_absent', 'args_present', 'absent']),
            path=dict(required=False, default='/etc/pam.d', type='str')
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
            ("state", "after", ["new_module_path"])

        ]
    )

    service = module.params['name']
    old_type = module.params['type']
    old_control = module.params['control']
    old_module_path = module.params['module_path']

    new_type = module.params['new_type']
    new_control = module.params['new_control']
    new_module_path = module.params['new_module_path']

    module_arguments = module.params['module_arguments']
    state = module.params['state']

    path = module.params['path']

    pamd = PamdService(module)
    pamd.load_rules_from_file()

    old_rule = PamdRule(old_type,
                        old_control,
                        old_module_path)
    new_rule = PamdRule(new_type,
                        new_control,
                        new_module_path,
                        module_arguments)

    if state == 'updated':
        change, result = update_rule(pamd,
                                     old_rule,
                                     new_rule)
    elif state == 'before':
        change, result = insert_before_rule(pamd,
                                            old_rule,
                                            new_rule)
    elif state == 'after':
        change, result = insert_after_rule(pamd,
                                           old_rule,
                                           new_rule)
    elif state == 'args_absent':
        change, result = remove_module_arguments(pamd,
                                                 old_rule,
                                                 module_arguments)
    elif state == 'args_present':
        change, result = add_module_arguments(pamd,
                                              old_rule,
                                              module_arguments)
    elif state == 'absent':
        change, result = remove_rule(pamd,
                                     old_rule)

    if not module.check_mode and change:
        pamd.write()

    facts = {}
    facts['pamd'] = {'changed': change, 'result': result}

    module.params['dest'] = pamd.fname

    module.exit_json(changed=change, ansible_facts=facts)

if __name__ == '__main__':
    main()
