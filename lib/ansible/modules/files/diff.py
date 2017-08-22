#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, cytopia <cytopia@everythingcli.org>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: diff
author:
    - cytopia (@cytopia)
short_description: Diff compare strings, files or command outputs
description:
    - Diff compare a string, file or command output against a string file or command output.
    - Check mode is only supported when diffing strings or files, commands will only be executed in actual run.
    - More examples at U(https://github.com/cytopia/ansible-modules)
version_added: "2.4"
options:
    source:
        description:
            - The source input to diff. Can be a string, contents of a file or output from a command, depending on I(source_type).
        required: true

    target:
        description:
            - The target input to diff. Can be a string, contents of a file or output from a command, depending on I(target_type).
        required: true

    source_type:
        description:
            - Specify the input type of I(source).
        required: true
        default: string
        choices: [ string, file, command ]

    target_type:
        description:
            - Specify the input type of I(target).
        required: true
        default: string
        choices: [ string, file, command ]
'''

EXAMPLES = '''
# Diff compare two strings
- diff:
    source: "foo"
    target: "bar"
    source_type: string
    target_type: string

# Diff compare variable against template file (as strings)
- diff:
    source: "{{ lookup('template', tpl.yml.j2) }}"
    target: "{{ my_var }}"
    source_type: string
    target_type: string

# Diff compare string against command output
- diff:
    source: "/bin/bash"
    target: "which bash"
    source_type: string
    target_type: command

# Diff compare file against command output
- diff:
    source: "/etc/hostname"
    target: "hostname"
    source_type: file
    target_type: command
'''

RETURN = '''
diff:
    description: diff output
    returned: success
    type: string
    sample: + this line was added
'''

# Python default imports
import os
import time
import subprocess

# Python Ansible imports
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def shell_exec(command):
    '''
    Execute raw shell command and return exit code and output
    '''
    cpt = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = []
    for line in iter(cpt.stdout.readline, ''):
        output.append(line)

    # Wait until process terminates (without using p.wait())
    while cpt.poll() is None:
        # Process hasn't exited yet, let's wait some
        time.sleep(0.5)

    # Get return code from process
    return_code = cpt.returncode

    # Return code and output
    return return_code, output


def diff_module_validation(module):
    '''
    Validate for correct module call/usage in ansible.
    '''
    source = module.params.get('source')
    target = module.params.get('target')
    source_type = module.params.get('source_type')
    target_type = module.params.get('target_type')

    # Validate source
    if source_type == 'file':
        b_source = to_bytes(source, errors='surrogate_or_strict')
        if not os.path.exists(b_source):
            module.fail_json(msg="source %s not found" % (source))
        if not os.access(b_source, os.R_OK):
            module.fail_json(msg="source %s not readable" % (source))
        if os.path.isdir(b_source):
            module.fail_json(msg="diff does not support recursive diff of directory: %s" % (source))

    # Validate target
    if target_type == 'file':
        b_target = to_bytes(target, errors='surrogate_or_strict')
        if not os.path.exists(b_target):
            module.fail_json(msg="target %s not found" % (target))
        if not os.access(b_target, os.R_OK):
            module.fail_json(msg="target %s not readable" % (target))
        if os.path.isdir(b_target):
            module.fail_json(msg="diff does not support recursive diff of directory: %s" % (target))

    return module


def main():
    '''
    Main function
    '''
    module = AnsibleModule(
        argument_spec=dict(
            source=dict(required=True, default=None, type='str'),
            target=dict(required=True, default=None, type='str'),
            source_type=dict(required=True, default='string',
                             choices=['string', 'file', 'command']),
            target_type=dict(required=True, default='string',
                             choices=['string', 'file', 'command']),
        ),
        supports_check_mode=True
    )

    # Validate module
    module = diff_module_validation(module)

    # Get ansible arguments
    source = module.params.get('source')
    target = module.params.get('target')
    source_type = module.params.get('source_type')
    target_type = module.params.get('target_type')

    # Source file to string
    if source_type == 'file':
        with open(source, 'rt') as fpt:
            source = fpt.read().decode("UTF-8")
    # Source command to string
    elif source_type == 'command':
        if module.check_mode:
            result = dict(
                changed=False,
                msg="This module does not support check mode when source_type is 'command'.",
                skipped=True
            )
            module.exit_json(**result)
        else:
            ret, source = shell_exec(source)
            if ret != 0:
                module.fail_json(msg="source command failed: %s" % (source))

    # Targe file to string
    if target_type == 'file':
        with open(target, 'rt') as fpt:
            target = fpt.read().decode("UTF-8")
    # Target command to string
    elif target_type == 'command':
        if module.check_mode:
            result = dict(
                changed=False,
                msg="This module does not support check mode when target_type is 'command'.",
                skipped=True
            )
            module.exit_json(**result)
        else:
            ret, target = shell_exec(target)
            if ret != 0:
                module.fail_json(msg="target command failed: %s" % (target))

    # Ansible diff output
    diff = {
        'before': target,
        'after': source,
    }
    # Did we have any changes?
    changed = (source != target)

    # Ansible module returned variables
    result = dict(
        diff=diff,
        changed=changed
    )

    # Exit ansible module call
    module.exit_json(**result)


if __name__ == '__main__':
    main()
