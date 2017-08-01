#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jimmy Tang <jcftang@gmail.com>
# Based on okpg (Patrick Pelletier <pp.pelletier@gmail.com>), pacman
# (Afterburn) and pkgin (Shaun Zinck) modules
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: macports
author: "Jimmy Tang (@jcftang)"
short_description: Package manager for MacPorts
description:
    - Manages MacPorts packages
version_added: "1.1"
options:
    name:
        description:
            - name of package to install/remove
        required: true
    state:
        description:
            - state of the package
        choices: [ 'present', 'absent', 'active', 'inactive' ]
        required: false
        default: present
    update_cache:
        description:
            - update the package db first
        required: false
        default: "no"
        choices: [ "yes", "no" ]
notes:  []
'''
EXAMPLES = '''
- macports:
    name: foo
    state: present

- macports:
    name: foo
    state: present
    update_cache: yes

- macports:
    name: foo
    state: absent

- macports:
    name: foo
    state: active

- macports:
    name: foo
    state: inactive
'''

import pipes

def update_package_db(module, port_path):
    """ Updates packages list. """

    rc, out, err = module.run_command("%s sync" % port_path)

    if rc != 0:
        module.fail_json(msg="could not update package db")


def query_package(module, port_path, name, state="present"):
    """ Returns whether a package is installed or not. """

    if state == "present":

        rc, out, err = module.run_command("%s installed | grep -q ^.*%s" % (pipes.quote(port_path), pipes.quote(name)), use_unsafe_shell=True)
        if rc == 0:
            return True

        return False

    elif state == "active":

        rc, out, err = module.run_command("%s installed %s | grep -q active" % (pipes.quote(port_path), pipes.quote(name)), use_unsafe_shell=True)

        if rc == 0:
            return True

        return False


def remove_packages(module, port_path, packages):
    """ Uninstalls one or more packages if installed. """

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, port_path, package):
            continue

        rc, out, err = module.run_command("%s uninstall %s" % (port_path, package))

        if query_package(module, port_path, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, port_path, packages):
    """ Installs one or more packages if not already installed. """

    install_c = 0

    for package in packages:
        if query_package(module, port_path, package):
            continue

        rc, out, err = module.run_command("%s install %s" % (port_path, package))

        if not query_package(module, port_path, package):
            module.fail_json(msg="failed to install %s: %s" % (package, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def activate_packages(module, port_path, packages):
    """ Activate a package if it's inactive. """

    activate_c = 0

    for package in packages:
        if not query_package(module, port_path, package):
            module.fail_json(msg="failed to activate %s, package(s) not present" % (package))

        if query_package(module, port_path, package, state="active"):
            continue

        rc, out, err = module.run_command("%s activate %s" % (port_path, package))

        if not query_package(module, port_path, package, state="active"):
            module.fail_json(msg="failed to activate %s: %s" % (package, out))

        activate_c += 1

    if activate_c > 0:
        module.exit_json(changed=True, msg="activated %s package(s)" % (activate_c))

    module.exit_json(changed=False, msg="package(s) already active")


def deactivate_packages(module, port_path, packages):
    """ Deactivate a package if it's active. """

    deactivated_c = 0

    for package in packages:
        if not query_package(module, port_path, package):
            module.fail_json(msg="failed to activate %s, package(s) not present" % (package))

        if not query_package(module, port_path, package, state="active"):
            continue

        rc, out, err = module.run_command("%s deactivate %s" % (port_path, package))

        if query_package(module, port_path, package, state="active"):
            module.fail_json(msg="failed to deactivated %s: %s" % (package, out))

        deactivated_c += 1

    if deactivated_c > 0:
        module.exit_json(changed=True, msg="deactivated %s package(s)" % (deactivated_c))

    module.exit_json(changed=False, msg="package(s) already inactive")


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(aliases=["pkg"], required=True),
            state = dict(default="present", choices=["present", "installed", "absent", "removed", "active", "inactive"]),
            update_cache = dict(default="no", aliases=["update-cache"], type='bool')
        )
    )

    port_path = module.get_bin_path('port', True, ['/opt/local/bin'])

    p = module.params

    if p["update_cache"]:
        update_package_db(module, port_path)

    pkgs = p["name"].split(",")

    if p["state"] in ["present", "installed"]:
        install_packages(module, port_path, pkgs)

    elif p["state"] in ["absent", "removed"]:
        remove_packages(module, port_path, pkgs)

    elif p["state"] == "active":
        activate_packages(module, port_path, pkgs)

    elif p["state"] == "inactive":
        deactivate_packages(module, port_path, pkgs)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
