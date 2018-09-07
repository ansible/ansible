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
notes:
    - Use C(environment) to influence Go with any other accepted environment variable
    - To utilize a C(go) binary in another path, utilize the C(PATH) environment variable via C(environment)
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
    go_path:
        description:
            - Path to be used for C(GOPATH), defaults to the target systems C(GOPATH) environment variable
requirements: []
short_description: Manage Go packages
version_added: 2.8
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

- name: Install a package in a specific GOPATH
  go:
    state: latest
    name: gopkg.in/yaml.v2
    go_path: /home/user/go
'''

RETURN = '''#
'''

import json
import shutil

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, env_fallback


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

    # When ``got get`` is run in verbose mode, if the package was installed/updated
    # stderr should end with ``(download)\n``
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

    clean_cmd = [
        go_bin,
        'clean',
        '-i',
    ]

    list_cmd = [
        go_bin,
        'list',
        '-json',
        '-e',
    ]

    rc = 0
    stdout = []
    stderr = []
    failed_pkgs = []
    found_pkgs = {}

    for name in module.params['name']:
        list_rc, list_stdout, list_stderr = module.run_command(list_cmd + [name])
        try:
            data = json.loads(list_stdout)
        except ValueError:
            data = {}

        err = data.get('Error', {}).get('Err', '')

        if list_rc != 0 or 'Error' in data:
            if err.startswith('cannot find package'):
                continue

            rc = 1
            failed_pkgs.append(name)
            stderr.append(err)
            stderr.append(list_stderr)
        else:
            found_pkgs[name] = data['Dir']

    for name, install_dir in found_pkgs.items():
        clean_rc, clean_stdout, clean_stderr = module.run_command(clean_cmd + [name])
        if clean_rc != 0:
            rc = clean_rc
        stdout.append(clean_stdout)
        stderr.append(clean_stderr)

        try:
            shutil.rmtree(install_dir)
        except Exception as e:
            failed_pkgs.append(name)
            stderr.append('Failed to remove %s: %s' % (install_dir, to_native(e)))
            rc = 1
        else:
            changed = True

    exit_args = {
        'rc': rc,
        'stdout': '\n'.join(l for l in stdout if l),
        'stderr': '\n'.join(l for l in stderr if l),
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
            go_path=dict(type='path', fallback=(env_fallback, ['GOPATH'])),
        )
    )
    env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')
    if module.params['go_path']:
        env['GOPATH'] = module.params['go_path']

    module.run_command_environ_update = env

    if module.params['state'] in ('present', 'latest', 'download'):
        rc, stdout, stderr, changed = install(module)
    else:
        rc, stdout, stderr, changed = uninstall(module)

    module.exit_json(rc=rc, stdout=stdout, stderr=stderr, changed=changed)


if __name__ == '__main__':
    main()
