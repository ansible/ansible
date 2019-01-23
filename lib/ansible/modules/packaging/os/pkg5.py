#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Peter Oliver <ansible@mavit.org.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: pkg5
author:
- Peter Oliver (@mavit)
short_description: Manages packages with the Solaris 11 Image Packaging System
version_added: '1.9'
description:
  - IPS packages are the native packages in Solaris 11 and higher.
notes:
  - The naming of IPS packages is explained at U(http://www.oracle.com/technetwork/articles/servers-storage-admin/ips-package-versioning-2232906.html).
options:
  name:
    description:
      - An FRMI of the package(s) to be installed/removed/updated.
      - Multiple packages may be specified, separated by C(,).
    required: true
  state:
    description:
      - Whether to install (I(present), I(latest)), or remove (I(absent)) a package.
    choices: [ absent, latest, present ]
    default: present
  accept_licenses:
    description:
      - Accept any licences.
    type: bool
    default: no
    aliases: [ accept, accept_licences ]
  be_name:
    description:
      - Creates a new boot environment with the given name.
    version_added: "2.8"
    type: str
  refresh:
    description:
      - Refresh publishers before execution.
    version_added: "2.8"
    type: bool
    default: yes
'''
EXAMPLES = '''
- name: Install Vim
  pkg5:
    name: editor/vim

- name: Install Vim without refreshing publishers
  pkg5:
    name: editor/vim
    refresh: no

- name: Remove finger daemon
  pkg5:
    name: service/network/finger
    state: absent

- name: Install several packages at once
  pkg5:
    name:
    - /file/gnu-findutils
    - /text/gnu-grep
'''

import re

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True),
            state=dict(type='str', default='present', choices=['absent', 'installed', 'latest', 'present', 'removed', 'uninstalled']),
            accept_licenses=dict(type='bool', default=False, aliases=['accept', 'accept_licences']),
            be_name=dict(type='str'),
            refresh=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    params = module.params
    packages = []

    # pkg(5) FRMIs include a comma before the release number, but
    # AnsibleModule will have split this into multiple items for us.
    # Try to spot where this has happened and fix it.
    for fragment in params['name']:
        if re.search(r'^\d+(?:\.\d+)*', fragment) and packages and re.search(r'@[^,]*$', packages[-1]):
            packages[-1] += ',' + fragment
        else:
            packages.append(fragment)

    if params['state'] in ['present', 'installed']:
        ensure(module, 'present', packages, params)
    elif params['state'] in ['latest']:
        ensure(module, 'latest', packages, params)
    elif params['state'] in ['absent', 'uninstalled', 'removed']:
        ensure(module, 'absent', packages, params)


def ensure(module, state, packages, params):
    response = {
        'results': [],
        'msg': '',
    }
    behaviour = {
        'present': {
            'filter': lambda p: not is_installed(module, p),
            'subcommand': 'install',
        },
        'latest': {
            'filter': lambda p: (
                not is_installed(module, p) or not is_latest(module, p)
            ),
            'subcommand': 'install',
        },
        'absent': {
            'filter': lambda p: is_installed(module, p),
            'subcommand': 'uninstall',
        },
    }

    if module.check_mode:
        dry_run = ['-n']
    else:
        dry_run = []

    if params['accept_licenses']:
        accept_licenses = ['--accept']
    else:
        accept_licenses = []

    if params['be_name']:
        beadm = ['--be-name=' + module.params['be_name']]
    else:
        beadm = []

    if params['refresh']:
        no_refresh = []
    else:
        no_refresh = ['--no-refresh']

    to_modify = filter(behaviour[state]['filter'], packages)
    if to_modify:
        rc, out, err = module.run_command(['pkg', behaviour[state]['subcommand']] + dry_run + accept_licenses + beadm + no_refresh + ['-q', '--'] + to_modify)
        response['rc'] = rc
        response['results'].append(out)
        response['msg'] += err
        response['changed'] = True
        if rc == 4:
            response['changed'] = False
            response['failed'] = False
        elif rc != 0:
            module.fail_json(**response)

    module.exit_json(**response)


def is_installed(module, package):
    rc, out, err = module.run_command(['pkg', 'list', '--', package])
    return not bool(int(rc))


def is_latest(module, package):
    rc, out, err = module.run_command(['pkg', 'list', '-u', '--', package])
    return bool(int(rc))


if __name__ == '__main__':
    main()
