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
  return_data_updates:
    description:
        - A dict of info to add to that passed to fail_json.
    required: False
    version_added: "2.3"
  return_data:
    description:
        - A dict of info to pass to fail_json, completely replacing any existing args.
    required: False
    version_added: "2.3"
  output_list:
    description:
        - >
        A list describing the intended output in order. Each dict has keys for 'where' and 'what'.
        'where' is one of 'stdout', 'stderr', 'nobuf_stdout', 'nobuf_stderr'.
        'what' is a string to be written to the output described by 'where'.
        The where options are normal buffered stdout/stderr, and nobuf_stdout/nobuf_stderr for unbuffered
        stdout/stderr. The later can be used to simulate intertwine stdout/stderr output from a module.
        The output is written in the order of the output_list.
    required: False
    version_added: "2.4"
  exception_type:
      description:
          - A name of a python exception to raise.
    required: False
    version_added: "2.4"
  exception_args:
      description:
          - A list of args to pass to exception_type
      required: False
      version_added: "2.4"
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
            return_data=dict(required=False, type='dict', default=None),
            return_data_updates=dict(required=False, type='dict', default={}),
            output_list=dict(required=False, type='list', default=[]),
            exception_type=dict(required=False, type='str', default=None),
            exception_args=dict(required=False, type='list', default=None),
            failure_mode=dict(required=False, type='str',
                              choices=['exit_json', 'fail_json', 'sys_exit', 'exception',
                                       'no_output', 'hang', 'python_traceback', 'incomplete_json'])
        ),
        supports_check_mode=True
    )

    stdout_text = module.params.get('stdout_text')
    stderr_text = module.params.get('stderr_text')
    return_code = module.params.get('return_code')
    failure_mode = module.params.get('failure_mode', 'fail_json')
    return_data_updates = module.params.get('return_data_updates', {})
    return_data = module.params.get('return_data', None)
    output_list = module.params.get('output_list', [])
    exception_type = module.params.get('exception_type', None)
    exception_args = module.params.get('exception_args', None)

    nobuf_stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    nobuf_stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

    # 37/0

    def nobuf_stdout_write(what):
        nobuf_stdout.write(what)
        nobuf_stdout.flush()

    def nobuf_stderr_write(what):
        nobuf_stderr.write(what)
        nobuf_stderr.flush()

    def stdout_write(what):
        sys.stdout.write(what)
        sys.stdout.flush()

    def stderr_write(what):
        sys.stderr.write(what)
        sys.stderr.flush()

    where_map = {'stdout': stdout_write,
                 'stderr': stderr_write,
                 'nobuf_stdout': nobuf_stdout_write,
                 'nobuf_stderr': nobuf_stderr_write}

    # A list of data indicating what to output to where and in what order. Useful for
    # interleaving stdout/stderr
    for output_info in output_list:
        where = output_info.get('where', 'stdout')
        what = output_info.get('what', None)
        # TODO: when?

        # call the writer method
        where_map[where](what)

    if stdout_text:
        nobuf_stdout.write(stdout_text)
        nobuf_stdout.flush()

    if stderr_text:
        nobuf_stderr.write(stderr_text)
        nobuf_stderr.flush()

    sys.stderr.flush()
    sys.stderr.flush()

    if failure_mode == 'exit_json':
        exit_data = {'changed': False,
                     'failed': False,
                     'msg': 'epic_fail did not live up to its name.',
                     'rc': return_code or 0}
        exit_data.update(return_data_updates)

        if return_data:
            exit_data = return_data

        module.exit_json(**exit_data)

    if failure_mode == 'fail_json':
        fail_data = {'rc': return_code or 1,
                     'failed': True}
        fail_data.update(return_data_updates)
        if return_data:
            fail_data = return_data
        module.fail_json(**fail_data)

    # exit sans fail_json or exit_json
    if failure_mode == 'sys_exit':
        sys.exit(return_code or 14)

    if failure_mode == 'exception':
        if not exception_type:
            module.fail_json(msg='Not very exceptional are we? If you want failure_mode=exception, you have to at least tell me the exception_type.')

        # lookup exception_type in scope
        exc = locals().get(exception_type, None) or globals().get(exception_type, None) or getattr(__builtins__, exception_type, None)
        if not exc:
            module.fail_json(msg='It is very exceptional of you to want to fail as %s,' % exception_type +
                             'but that is not even a thing.  ' +
                             'a thing in locals, globals, or builtins. Next time maybe try an exception that exists.')
        exc_args = exception_args or []
        try:
            exc_instance = exc(*exception_args)
        except Exception as e:
            raise
            module.fail_json(msg='There are rules man! Also, your argument is invalid. I tried to make an exception for you, but all it got me was: %s' % e)
        raise exc_instance
    # TODO: implement other failure modes

    module.fail_json(msg='You haved failed at failing. End of epic_fail reached.')


if __name__ == '__main__':
    main()
