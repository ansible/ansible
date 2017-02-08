#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 Adrian Likins <alikins@redhat.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

#
ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: epic_fail
short_description: Fail in exciting ways for testing.
description:
     - This module will fail in ways ansible does not expect.

version_added: "2.3"
options:
  stdout_text:
    description:
      - If provided, this will be printed to stdout instead of json
    required: false
    version_added: "2.3"
  stderr_text:
    description:
      - If provided, this will be printed to stderr.
    required: False
    version_added: "2.3"
  return_code:
    description:
      - A number for the return code the module will exit with.
    required: False
    default: 0
    version_added: "2.3"
  failure_mode:
    description:
        - The type of failure to emulated.
    required: False
    version_added: "2.3"
  output_data_updates:
    description:
        - A dict of info to add to that passed to fail_json.
    required: False
    version_added: "2.3"
  output_data_replacement:
    description:
        - A dict of info to pass to fail_json, completely replacing any existing args.
    required: False
    version_added: "2.3"
author:
    - "Adrian Likins <alikins@redhat.com>"
'''

EXAMPLES = '''
# Example of garbage stdout
- epic_fail:
    stdout_text: "/bin/bash not found"

# Example of letting normal json be returned but with a non-0 exit
  epic_fail:
    return_code: 11

  register: result

'''

import os
import sys

from ansible.module_utils.basic import AnsibleModule

SYS_EXIT = 'sys_exit'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            stdout_text=dict(required=False, type='str'),
            stderr_text=dict(required=False, type='str'),
            return_code=dict(required=False, type='int'),
            output_data=dict(required=False, type='dict'),
            failure_mode=dict(required=False, type='str',
                              choices=['sys_exit', 'no_output', 'hang', 'python_traceback', 'incomplete_json'])
        ),
        supports_check_mode=True
    )

    stdout_text = module.params.get('stdout_text')
    stderr_text = module.params.get('stderr_text')
    return_code = module.params.get('return_code')
    failure_mode = module.params.get('failure_mode')
    output_data_updates = module.params.get('output_data_updates', {})
    output_data_replacement = module.params.get('output_data_replacement', None)

    sys_exit = None

    nobuf_stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    nobuf_stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

    if failure_mode == SYS_EXIT:
        sys_exit = True

    if stdout_text:
        nobuf_stdout.write(stdout_text)
        nobuf_stdout.flush()

    if stderr_text:
        nobuf_stderr.write(stderr_text)
        nobuf_stderr.flush()

    sys.stderr.flush()
    sys.stderr.flush()

    # exit sans fail_json or exit_json
    if sys_exit:
        sys.exit(return_code or 14)

    # TODO: implement modes

    if return_code:
        fail_data = dict(msg='epic_fail failed with a return code of %s just as its parents predicted.' % return_code,
                         blip=return_code,
                         rc=return_code)
        fail_data.update(output_data_updates)
        if output_data_replacement:
            fail_data = output_data_replacement
        module.fail_json(**fail_data)

    # fail in a boring fashion
    fail_data = dict(msg="epic_fail failed in a non epic fashion. How typical.")
    fail_data.update(output_data_updates)
    if output_data_replacement:
        fail_data = output_data_replacement
    module.fail_json(**fail_data)

    exit_data = dict(changed=False,
                     msg="epic_fail did not live up to its name.")
    exit_data.update(output_data_updates)
    if output_data_replacement:
        exit_data = output_data_replacement
    module.exit_json(**exit_data)


if __name__ == '__main__':
    main()
