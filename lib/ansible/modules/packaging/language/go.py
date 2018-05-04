#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
author: 'Matt Martz (@sivel)'
description:
    - Manage Go packages
module: go
notes: []
options:
    name:
        description:
            - Name of Go package to install
        required: true
    state:
        choices:
            - present
            - absent
            - latest
            - download
        default: present
        description:
            - Desired state of the package. C(download) will download the package, but will not install the package.
    validate_certs:
        default: true
        description:
            - Whether or not to validate SSL certificates when downloading packages
        type: bool
requirements: []
short_description: Manage Go packages
version_added: 2.6.0
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

EXAMPLES = '''
- name: Install gopkg.in/yaml.v2
  go:
    state: present
    name: gopkg.in/yaml.v2

- name: Install multiple packages
  go:
    state: present
    name:
      - gopkg.in/yaml.v1
      - gopkg.in/yaml.v2

- name: Remove a package
  go:
    state: absent
    name: gopkg.in/yaml.v2

- name: Upgrade a package
  go:
    state: latest
    name: gopkg.in/yaml.v2
'''

RETURN = '''#
'''

import json
import shutil

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule


def install(module):
    go_bin = module.get_bin_path('go', required=True)
    cmd = [
        go_bin,
        'get',
        '-v',
    ]

    if module.params['state'] == 'download':
        cmd.append('-d')
    elif module.params['state'] == 'latest':
        cmd.append('-u')

    if not module.params['validate_certs']:
        cmd.append('-insecure')

    cmd.extend(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    changed = stderr and not stderr.endswith('(download)\n')

    exit_args = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
        'changed': changed,
    }

    if rc:
        msg = 'Failed to install packages'
        module.fail_json(msg=msg, **exit_args)
    else:
        module.exit_json(**exit_args)


def uninstall(module):
    changed = False
    go_bin = module.get_bin_path('go', required=True)
    cmd = [
        go_bin,
        'clean',
        '-i',
    ]
    rc = 0
    stdout = ''
    stderr = ''
    failed_pkgs = []
    found_pkgs = []

    for name in module.params['name']:
        _rc, _stdout, _stderr = module.run_command(cmd + [name])
        if _rc == 1 and 'cannot find package' in _stderr:
            continue
        else:
            if _rc != 0:
                rc = _rc
                failed_pkgs.append(name)
            else:
                found_pkgs.append(name)
            stdout += _stdout
            stderr += _stderr

    list_cmd = [
        go_bin,
        'list',
        '-json',
    ]

    for name in found_pkgs:
        list_rc, list_stdout, list_stderr = module.run_command(list_cmd + [name])
        if list_rc == 1 and 'no Go files' in list_stderr:
            continue
        elif list_rc != 0:
            failed_pkgs.append(name)
            stdout += list_stdout
            stderr += list_stderr
            rc = 1
            continue

        data = json.loads(list_stdout)

        try:
            shutil.rmtree(data['Dir'])
        except Exception as e:
            failed_pkgs.append(name)
            stderr += '%s: %s' % (data['Dir'], to_native(e))
            rc = 1
        else:
            changed = True

    exit_args = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
        'changed': changed,
    }

    if rc:
        msg = 'Failed to remove %s' % (', '.join(failed_pkgs),)
        module.fail_json(msg=msg, **exit_args)
    else:
        module.exit_json(**exit_args)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True),
            state=dict(type='str', choices=['present', 'absent', 'latest', 'download'], default='present'),
            validate_certs=dict(type='bool', default=True),
        )
    )
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    if module.params['state'] in ('present', 'latest', 'download'):
        rc, stdout, stderr, changed = install(module)
    else:
        rc, stdout, stderr, changed = uninstall(module)

    module.exit_json(rc=rc, stdout=stdout, stderr=stderr, changed=changed)


if __name__ == '__main__':
    main()
