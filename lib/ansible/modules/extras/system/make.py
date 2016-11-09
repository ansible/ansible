#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: make
short_description: Run targets in a Makefile
requirements: [ make ]
version_added: "2.1"
author: Linus Unnebäck (@LinusU) <linus@folkdatorn.se>
description:
  - Run targets in a Makefile.
options:
  target:
    description:
      - The target to run
    required: false
    default: none
  params:
    description:
      - Any extra parameters to pass to make
    required: false
    default: none
  chdir:
    description:
      - cd into this directory before running make
    required: true
'''

EXAMPLES = '''
# Build the default target
- make: chdir=/home/ubuntu/cool-project

# Run `install` target as root
- make: chdir=/home/ubuntu/cool-project target=install
  become: yes

# Pass in extra arguments to build
- make:
    chdir: /home/ubuntu/cool-project
    target: all
    params:
      NUM_THREADS: 4
      BACKEND: lapack
'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule


def run_command(command, module, check_rc=True):
    """
    Run a command using the module, return
    the result code and std{err,out} content.

    :param command: list of command arguments
    :param module: Ansible make module instance
    :return: return code, stdout content, stderr content
    """
    rc, out, err = module.run_command(command, check_rc=check_rc, cwd=module.params['chdir'])
    return rc, sanitize_output(out), sanitize_output(err)


def sanitize_output(output):
    """
    Sanitize the output string before we
    pass it to module.fail_json. Defaults
    the string to empty if it is None, else
    strips trailing newlines.

    :param output: output to sanitize
    :return: sanitized output
    """
    if output is None:
        return ''
    else:
        return output.rstrip("\r\n")


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            target=dict(required=False, default=None, type='str'),
            params=dict(required=False, default=None, type='dict'),
            chdir=dict(required=True, default=None, type='path'),
        ),
    )
    # Build up the invocation of `make` we are going to use
    make_path = module.get_bin_path('make', True)
    make_target = module.params['target']
    if module.params['params'] is not None:
        make_parameters = [k + '=' + str(v) for k, v in iteritems(module.params['params'])]
    else:
        make_parameters = []

    base_command = [make_path, make_target]
    base_command.extend(make_parameters)

    # Check if the target is already up to date
    rc, out, err = run_command(base_command + ['--question'], module, check_rc=False)
    if module.check_mode:
        # If we've been asked to do a dry run, we only need
        # to report whether or not the target is up to date
        changed = (rc != 0)
    else:
        if rc == 0:
            # The target is up to date, so we don't have to
            #  do anything
            changed = False
        else:
            # The target isn't upd to date, so we need to run it
            rc, out, err = run_command(base_command, module)
            changed = True

    # We don't report the return code, as if this module failed
    # we would be calling fail_json from run_command, so even if
    # we had a non-zero return code, we did not fail. However, if
    # we report a non-zero return code here, we will be marked as
    # failed regardless of what we signal using the failed= kwarg.
    module.exit_json(
        changed=changed,
        failed=False,
        stdout=out,
        stderr=err,
        target=module.params['target'],
        params=module.params['params'],
        chdir=module.params['chdir']
    )


if __name__ == '__main__':
    main()
