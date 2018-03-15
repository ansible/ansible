#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Linus Unnebäck <linus@folkdatorn.se>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  params:
    description:
      - Any extra parameters to pass to make
  chdir:
    description:
      - cd into this directory before running make
    required: true
  file:
    description:
      - Use file as a Makefile
    version_added: 2.5
'''

EXAMPLES = '''
# Build the default target
- make:
    chdir: /home/ubuntu/cool-project

# Run `install` target as root
- make:
    chdir: /home/ubuntu/cool-project
    target: install
  become: yes

# Pass in extra arguments to build
- make:
    chdir: /home/ubuntu/cool-project
    target: all
    params:
      NUM_THREADS: 4
      BACKEND: lapack

# Pass a file as a Makefile
- make:
    chdir: /home/ubuntu/cool-project
    target: all
    file: /some-project/Makefile
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
            file=dict(required=False, default=None, type='path')
        ),
    )
    # Build up the invocation of `make` we are going to use
    make_path = module.get_bin_path('make', True)
    make_target = module.params['target']
    if module.params['params'] is not None:
        make_parameters = [k + '=' + str(v) for k, v in iteritems(module.params['params'])]
    else:
        make_parameters = []

    if module.params['file'] is not None:
        base_command = [make_path, "--file", module.params['file'], make_target]
    else:
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
        chdir=module.params['chdir'],
        file=module.params['file']
    )


if __name__ == '__main__':
    main()
