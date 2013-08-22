#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2012, Afterburn
# Written by Afterburn <http://github.com/afterburn> 
# Based on apt module written by Matthew Williams <matthew@flowroute.com>
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
module: pacman
short_description: Package manager for Archlinux
description:
    - Manages Archlinux packages

version_added: "1.0"
options:
    name:
        description:
            - name of package to install, upgrade or remove.
        required: true

    state:
        description:
            - state of the package (installed or absent).
        required: false

    update_cache:
        description:
            - update the package database first (pacman -Syy).
        required: false
        default: "no"
        choices: [ "yes", "no" ]

    recurse:
        description:
            - remove all not explicitly installed dependencies not required
              by other packages of the package to remove
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        version_added: "1.3"

author: Afterburn
notes:  []
'''

EXAMPLES = '''
# Install package foo
- pacman: name=foo state=installed

# Remove package foo
- pacman: name=foo state=absent

# Remove packages foo and bar 
- pacman: name=foo,bar state=absent

# Recursively remove package baz
- pacman: name=baz state=absent recurse=yes

# Update the package database (pacman -Syy) and install bar (bar will be the updated if a newer version exists) 
- pacman: name=bar, state=installed, update_cache=yes
'''


import json
import shlex
import os
import re
import sys

PACMAN_PATH = "/usr/bin/pacman"

def query_package(module, name, state="installed"):

    # pacman -Q returns 0 if the package is installed,
    # 1 if it is not installed
    if state == "installed":
        rc = os.system("pacman -Q %s" % (name))

        if rc == 0:
            return True

        return False


def update_package_db(module):
    rc = os.system("pacman -Syy > /dev/null")

    if rc != 0:
        module.fail_json(msg="could not update package db")
         

def remove_packages(module, packages):
    if module.params["recurse"]:
        args = "Rs"
    else:
        args = "R"
    
    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package):
            continue

        rc = os.system("pacman -%s %s --noconfirm > /dev/null" % (args, package))

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))
    
        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, packages, package_files):

    install_c = 0

    for i, package in enumerate(packages):
        if query_package(module, package):
            continue

        if package_files[i]:
            params = '-U %s' % package_files[i]
        else:
            params = '-S %s' % package

        rc = os.system("pacman %s --noconfirm > /dev/null" % (params))

        if rc != 0:
            module.fail_json(msg="failed to install %s" % (package))

        install_c += 1
    
    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already installed")


def check_packages(module, packages, state):
    would_be_changed = []
    for package in packages:
        installed = query_package(module, package)
        if ((state == "installed" and not installed) or
                (state == "absent" and installed)):
            would_be_changed.append(package)
    if would_be_changed:
        if state == "absent":
            state = "removed"
        module.exit_json(changed=True, msg="%s package(s) would be %s" % (
            len(would_be_changed), state))
    else:
        module.exit_json(change=False, msg="package(s) already %s" % state)


def main():
    module = AnsibleModule(
            argument_spec    = dict(
                state        = dict(default="installed", choices=["installed","absent"]),
                update_cache = dict(default="no", aliases=["update-cache"], type='bool'),
                recurse      = dict(default="no", type='bool'),
                name         = dict(aliases=["pkg"], required=True)),
            supports_check_mode = True)
                

    if not os.path.exists(PACMAN_PATH):
        module.fail_json(msg="cannot find pacman, looking for %s" % (PACMAN_PATH))

    p = module.params

    if p["update_cache"] and not module.check_mode:
        update_package_db(module)

    pkgs = p["name"].split(",")

    pkg_files = []
    for i, pkg in enumerate(pkgs):
        if pkg.endswith('.pkg.tar.xz'):
            # The package given is a filename, extract the raw pkg name from
            # it and store the filename
            pkg_files.append(pkg)
            pkgs[i] = re.sub('-[0-9].*$', '', pkgs[i].split('/')[-1])
        else:
            pkg_files.append(None)

    if module.check_mode:
        check_packages(module, pkgs, p['state'])

    if p["state"] == "installed":
        install_packages(module, pkgs, pkg_files)

    elif p["state"] == "absent":
        remove_packages(module, pkgs)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
    
main()        
