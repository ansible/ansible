#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrick Pelletier <pp.pelletier@gmail.com>
# Based on pacman (Afterburn) and pkgin (Shaun Zinck) modules
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
module: opkg
author: Patrick Pelletier
short_description: Package manager for OpenWrt
description:
    - Manages OpenWrt packages
version_added: "1.1"
options:
    name:
        description:
            - name of package to install/remove
        required: true
    state:
        description:
            - state of the package
        choices: [ 'present', 'absent' ]
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
- opkg: name=foo state=present
- opkg: name=foo state=present update_cache=yes
- opkg: name=foo state=absent
- opkg: name=foo,bar state=absent
'''

import pipes

def update_package_db(module, opkg_path):
    """ Updates packages list. """

    rc, out, err = module.run_command("%s update" % opkg_path)

    if rc != 0:
        module.fail_json(msg="could not update package db")


def query_package(module, opkg_path, name, state="present"):
    """ Returns whether a package is installed or not. """

    if state == "present":

        rc, out, err = module.run_command("%s list-installed | grep -q \"^%s \"" % (pipes.quote(opkg_path), pipes.quote(name)), use_unsafe_shell=True)
        if rc == 0:
            return True

        return False


def remove_packages(module, opkg_path, packages):
    """ Uninstalls one or more packages if installed. """

    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, opkg_path, package):
            continue

        rc, out, err = module.run_command("%s remove %s" % (opkg_path, package))

        if query_package(module, opkg_path, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, opkg_path, packages):
    """ Installs one or more packages if not already installed. """

    install_c = 0

    for package in packages:
        if query_package(module, opkg_path, package):
            continue

        rc, out, err = module.run_command("%s install %s" % (opkg_path, package))

        if not query_package(module, opkg_path, package):
            module.fail_json(msg="failed to install %s: %s" % (package, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(aliases=["pkg"], required=True),
            state = dict(default="present", choices=["present", "installed", "absent", "removed"]),
            update_cache = dict(default="no", aliases=["update-cache"], type='bool')
        )
    )

    opkg_path = module.get_bin_path('opkg', True, ['/bin'])

    p = module.params

    if p["update_cache"]:
        update_package_db(module, opkg_path)

    pkgs = p["name"].split(",")

    if p["state"] in ["present", "installed"]:
        install_packages(module, opkg_path, pkgs)

    elif p["state"] in ["absent", "removed"]:
        remove_packages(module, opkg_path, pkgs)

# import module snippets
from ansible.module_utils.basic import *

main()
