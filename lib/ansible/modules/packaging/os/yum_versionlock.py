#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Florian Paul Hoberg <florian.hoberg@credativ.de>
# Written by Florian Paul Hoberg <florian.hoberg@credativ.de>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: yum_versionlock
version_added: 2.7
short_description: Locks/Unlocks an installed package(s) from being updates by (yum) package manager.
description:
     - This module adds installed packages to yum versionlock to prevent it from being updated.
options:
  package:
    description:
      - Package name(s) like C(httpd). Multiple packages are supported by adding them by whitespaces.
  state:
    description:
      - Whether to lock C(present) or unlock C(absent) package(s).
    choices: [ present, absent ]
    default: present
# informational: requirements for nodes
requirements:
- yum
- yum-versionlock
author:
    - '"Florian Paul Hoberg (@florianpaulhoberg)" <florian.hoberg@credativ.de>'
'''

EXAMPLES = '''
- name: Prevent Apache / httpd from being updated
  yum_versionlock:
    state: present
    package: httpd
- name: Prevent multiple packages from being updated
  yum_versionlock:
    state: present
    package: httpd nginx haproxy curl
- name:  Unlock Apache / httpd to be updated again
  yum_versionlock:
    state: absent
    package: httpd
'''

RETURN = '''
package:
    description: name of used package
    returned: everytime
    type: string
    sample: httpd
state:
    description: state of used package
    returned: everytime
    type: string
    sample: present
'''

from ansible.module_utils.basic import AnsibleModule


def get_yum_path(module):
    """ Get yum path """
    yum_binary = module.get_bin_path('yum')
    return yum_binary


def get_state_yum_versionlock(module, yum_binary):
    """ Check for yum plugin dependency """
    rc_code, out, err = module.run_command("%s -q info yum-plugin-versionlock"
                                           % (yum_binary))
    if rc_code == 0:
        return out
    else:
        module.fail_json(msg="Error: Please install rpm package yum-plugin-versionlock | " + str(err) + str(out))


def get_versionlock_packages(module, yum_binary):
    """ Get an overview of all packages on yum versionlock """
    rc_code, out, err = module.run_command("%s -q versionlock list"
                                           % (yum_binary))
    if rc_code == 0:
        return out
    else:
        module.fail_json(msg="Error: " + str(err) + str(out))


def add_package_versionlock(module, package, yum_binary):
    """ Add package to yum versionlock """
    rc_code, out, err = module.run_command("%s -q versionlock add %s"
                                           % (yum_binary, package))
    if rc_code == 0:
        changed = True
        return changed
    else:
        module.fail_json(msg="Error: " + str(err) + str(out))


def remove_package_versionlock(module, package, yum_binary):
    """ Remove package from yum versionlock """
    rc_code, out, err = module.run_command("%s -q versionlock delete %s"
                                           % (yum_binary, package))
    if rc_code == 0:
        changed = True
        return changed
    else:
        module.fail_json(msg="Error: " + str(err) + str(out))


def main():
    """ start main program to add/remove a package to yum versionlock"""
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            package=dict(required=True, type='str'),
        ),
        supports_check_mode=False
    )

    state = module.params['state']
    package = module.params['package']
    changed = False

    # Get yum path
    yum_binary = get_yum_path(module)

    # Check for yum version lock plugin
    get_state_yum_versionlock(module, yum_binary)

    # Split 'package' string to list by whitespaces to support multiple values
    packages = package.split()

    # Get an overview of all packages that have a version lock
    versionlock_packages = get_versionlock_packages(module, yum_binary)

    # Add package(s) to versionlock
    if state == "present":
        for single_pkg in packages:
            if single_pkg not in versionlock_packages:
                changed = add_package_versionlock(module, single_pkg, yum_binary)

    # Remove package(s) from versionlock
    if state == "absent":
        for single_pkg in packages:
            if single_pkg in versionlock_packages:
                changed = remove_package_versionlock(module, single_pkg, yum_binary)

    # Create Ansible meta output
    response = {"package": package, "state": state}
    if changed is True:
        module.exit_json(changed=True, meta=response)
    else:
        module.exit_json(changed=False, meta=response)


if __name__ == '__main__':
    main()
