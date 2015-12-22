#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Peter Oliver <ansible@mavit.org.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: pkg5
author: "Peter Oliver (@mavit)"
short_description: Manages packages with the Solaris 11 Image Packaging System
version_added: 1.9
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
      - Whether to install (I(present), I(latest)), or remove (I(absent)) a
        package.
    required: false
    default: present
    choices: [ present, latest, absent ]
  accept_licenses:
    description:
      - Accept any licences.
    required: false
    default: false
    choices: [ true, false ]
    aliases: [ accept_licences, accept ]
'''
EXAMPLES = '''
# Install Vim:
- pkg5: name=editor/vim

# Remove finger daemon:
- pkg5: name=service/network/finger state=absent

# Install several packages at once:
- pkg5:
    name:
      - /file/gnu-findutils
      - /text/gnu-grep
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='list'),
            state=dict(
                default='present',
                choices=[
                    'present',
                    'installed',
                    'latest',
                    'absent',
                    'uninstalled',
                    'removed',
                ]
            ),
            accept_licenses=dict(
                type='bool',
                default=False,
                aliases=['accept_licences', 'accept'],
            ),
        )
    )

    params = module.params
    packages = []

    # pkg(5) FRMIs include a comma before the release number, but
    # AnsibleModule will have split this into multiple items for us.
    # Try to spot where this has happened and fix it.
    for fragment in params['name']:
        if (
            re.search('^\d+(?:\.\d+)*', fragment)
            and packages and re.search('@[^,]*$', packages[-1])
        ):
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
            'filter': lambda p: not is_latest(module, p),
            'subcommand': 'install',
        },
        'absent': {
            'filter': lambda p: is_installed(module, p),
            'subcommand': 'uninstall',
        },
    }

    if params['accept_licenses']:
        accept_licenses = ['--accept']
    else:
        accept_licenses = []

    to_modify = filter(behaviour[state]['filter'], packages)
    if to_modify:
        rc, out, err = module.run_command(
            [
                'pkg', behaviour[state]['subcommand']
            ]
            + accept_licenses
            + [
                '-q', '--'
            ] + to_modify
        )
        response['rc'] = rc
        response['results'].append(out)
        response['msg'] += err
        response['changed'] = True
        if rc != 0:
            module.fail_json(**response)

    module.exit_json(**response)


def is_installed(module, package):
    rc, out, err = module.run_command(['pkg', 'list', '--', package])
    return not bool(int(rc))


def is_latest(module, package):
    rc, out, err = module.run_command(['pkg', 'list', '-u', '--', package])
    return bool(int(rc))


from ansible.module_utils.basic import *
main()
