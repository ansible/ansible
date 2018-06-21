#!/usr/bin/env python

# Copyright (c) 2018, Florian Paul Hoberg <florian.hoberg@credativ.de>

import os.path
from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: yum_versionlock
short_description: Locks/prevents an installed package from beeing updates by yum
description:
  - This module adds installed packages to yum versionlock to prevent it from beeing updated.
    To run this module you need to install rpm package 'yum-versionlock'.
options:
  state:
    description:
      - Adds/removes a package to yum versionlock to prevent it from beeing updated
  package:
    description:
      - Wildcard package name (e.g. 'httpd')
author:
- Florian Paul Hoberg <florian.hoberg@credativ.de>
'''
EXAMPLES = '''
- name: Prevent Apache / httpd from beeing updated
  yum_versionlock:
    state: present
    package: httpd
'''

yum_binary = "/bin/yum"


def get_state_yum_versionlock():
    state = os.path.exists("/etc/yum/pluginconf.d/versionlock.conf")
    return state


def get_overview_versionlock_packages(module):
    """ Get an overview of all packages on yum versionlock """
    rc, out, err = module.run_command("%s -q versionlock list"
                                      % (yum_binary))
    if rc is 0: 
        return out
    else:
        module.fail_json(msg="Error: " + str(err))


def add_package_versionlock(module, package):
    """ Add package to yum versionlock """
    rc, out, err = module.run_command("%s -q versionlock add %s"
                                      % (yum_binary, package))
    if rc is 0: 
        changed = True
        return changed
    else:
        module.fail_json(msg="Error: " + str(err))


def remove_package_versionlock(module, package):
    """ Remove package from yum versionlock """
    rc, out, err = module.run_command("%s -q versionlock delete %s"
                                      % (yum_binary, package))
    if rc is 0: 
        changed = True
        return changed
    else:
        module.fail_json(msg="Error: " + str(err))


def main():
    """ start main program to add/remove a package to yum versionlock"""
    module = AnsibleModule(
        argument_spec       = dict(
            state         = dict(required=True, type='str'),
            package        = dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )

    state       = module.params['state']
    package      = module.params['package']
    changed = False

    # Check for yum version lock plugin
    versionlock_plugin = get_state_yum_versionlock()
    if versionlock_plugin is False:
        module.fail_json(msg="Error: Please install yum-versionlock")

    # Get an overview of all packages that have a version lock
    versionlock_packages = get_overview_versionlock_packages(module) 

    # Add a package to versionlock
    if state == "present":
        if not package in versionlock_packages:
            changed = add_package_versionlock(module, package)

    # Remove a package from versionlock
    if state == "absent":
        if package in versionlock_packages:
            changed = remove_package_versionlock(module, package)

    # Create Ansible meta output
    response = {"package": package, "state": state}
    if changed is True:
        module.exit_json(changed=True, meta=response)
    else:
        module.exit_json(changed=False, meta=response)


if __name__ == '__main__':
    main()
