#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import sys

from ansible.module_utils.basic import AnsibleModule

SYS_EXIT = 'sys_exit'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            stdout_text=dict(required=False, type='str'),
            stderr_text=dict(required=False, type='str'),
            return_code=dict(required=False, type='int'),
            failure_mode=dict(required=False, type='str',
                              choices=['sys_exit', 'no_output', 'hang', 'python_traceback', 'incomplete_json'])
        ),
        supports_check_mode=True
    )

    stdout_text = module.params.get('stdout_text')
    stderr_text = module.params.get('stderr_text')
    return_code = module.params.get('return_code')
    failure_mode = module.params.get('failure_mode')

    sys_exit = None

    if failure_mode == SYS_EXIT:
        sys_exit = True

    if stdout_text:
        sys.stdout.write(stdout_text)

    if stderr_text:
        sys.stderr.write(stderr_text)

    if sys_exit:
        sys.exit(return_code or 1)

    # TODO: implement modes

    if return_code:
        module.fail_json(msg='epic_fail failed with a return code of %s just as its parents predicted.' % return_code,
                         rc=return_code)

    # fail in a boring fashion
    module.fail_json(msg="epic_fail failed in a non epic fashion. How typical.")

    module.exit_json(changed=False,
                     msg="epic_fail did not live up to its name.")


if __name__ == '__main__':
    main()
