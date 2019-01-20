#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Raul Melo (@melodous) <raulmelo@gmail.com>
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# Based on yum module written by Seth Vidal <skvidal at fedoraproject.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: swdepot
short_description: Manage packages using the swdepot package manager (HP-UX)
description:
- Will install, upgrade and remove packages with the swdepot package manager (HP-UX).
version_added: '1.4'
author:
- Raul Melo (@melodous)
options:
  name:
    description:
    - The name of the package.
    type: str
    required: true
  state:
    description:
    - Whether to ensure the package is installed, the latest version or uninstalled.
    type: str
    choices: [ absent, latest, present ]
    default: present
  depot:
    description:
    - The source repository from which to install or upgrade a package.
    type: str
'''

EXAMPLES = r'''
- name: Ensure the unzip package version 6.0 is installed
  swdepot:
    name: unzip-6.0
    depot: repository:/path
    state: present

- name: Ensure the latest unzip package is installed
  swdepot:
    name: unzip
    depot: repository:/path
    state: latest

- name: Ensure the unzip package is not installed
  swdepot:
    name: unzip
    state: absent
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import shlex_quote


def compare_package(version1, version2):
    """ Compare version packages.
        Return values:
        -1 first minor
        0 equal
        1 first greater """

    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    normalized_version1 = normalize(version1)
    normalized_version2 = normalize(version2)
    if normalized_version1 == normalized_version2:
        rc = 0
    elif normalized_version1 < normalized_version2:
        rc = -1
    else:
        rc = 1
    return rc


def query_package(module, name, depot=None):
    """ Returns whether a package is installed or not and version. """

    cmd_list = '/usr/sbin/swlist -a revision -l product'
    if depot:
        rc, stdout, stderr = module.run_command("%s -s %s %s | grep %s" % (cmd_list, shlex_quote(depot), shlex_quote(name), shlex_quote(name)),
                                                use_unsafe_shell=True)
    else:
        rc, stdout, stderr = module.run_command("%s %s | grep %s" % (cmd_list, shlex_quote(name), shlex_quote(name)), use_unsafe_shell=True)
    if rc == 0:
        version = re.sub(r"\s\s+|\t", " ", stdout).strip().split()[1]
    else:
        version = None

    return rc, version


def remove_package(module, name):
    """ Uninstall package if installed. """

    cmd_remove = '/usr/sbin/swremove'
    rc, stdout, stderr = module.run_command("%s %s" % (cmd_remove, name))
    if rc == 0:
        return rc, stdout

    return rc, stderr


def install_package(module, depot, name):
    """ Install package if not already installed """

    cmd_install = '/usr/sbin/swinstall -x mount_all_filesystems=false'
    rc, stdout, stderr = module.run_command("%s -s %s %s" % (cmd_install, depot, name))
    if rc == 0:
        return rc, stdout

    return rc, stderr


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['pkg']),
            state=dict(type='str', default='present', choices=['absent', 'latest', 'present']),
            depot=dict(type='str'),
        ),
        required_if=[
            ['state', 'present', ['depot']],
            ['state', 'latest', ['depot']],
        ],
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    depot = module.params['depot']

    result = dict(
        changed=False,
        msg='No changes',
        name=name,
        rc=0,
    )

    # Check local version
    result['rc'], version_installed = query_package(module, name)
    if result['rc']:
        installed = False
    else:
        installed = True
        result['msg'] = 'Already installed'

    if (state == 'present' or state == 'latest') and installed is False:
        if not module.check_mode:
            # Install package
            result['rc'], result['msg'] = install_package(module, depot, name)
            if result['rc']:
                module.fail_json(**result)

        result['changed'] = True
        result['msg'] = 'Package installed'

    elif state == 'latest' and installed is True:
        # Check depot version
        result['rc'], version_depot = query_package(module, name, depot)

        if result['rc']:
            result['msg'] = 'Software package not in repository %s' % depot
            module.fail_json(**result)

        if compare_package(version_installed, version_depot) == -1:
            if not module.check_mode:
                # Install new version
                result['rc'], result['msg'] = install_package(module, depot, name)
                if result['rc']:
                    module.fail_json(**result)

            result['changed'] = True
            result['msg'] = 'Package upgraded, Before %s, Now %s' % (version_installed, version_depot)

    elif state == 'absent' and installed is True:
        if not module.check_mode:
            # Remove existing version
            result['rc'], result['msg'] = remove_package(module, name)
            if result['rc']:
                module.fail_json(**result)

        result['changed'] = True
        result['msg'] = 'Package removed'

    module.exit_json(state=state, **result)


if __name__ == '__main__':
    main()
