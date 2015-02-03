#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2012, Afterburn <http://github.com/afterburn>
# (c) 2013, Aaron Bull Schaefer <aaron@elasticdog.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: pacman
short_description: Manage packages with I(pacman)
description:
    - Manage packages with the I(pacman) package manager, which is used by
      Arch Linux and its variants.
version_added: "1.0"
author: Afterburn
notes: []
requirements: []
options:
    name:
        description:
            - Name of the package to install, upgrade, or remove.
        required: false
        default: null

    state:
        description:
            - Desired state of the package.
        required: false
        default: "present"
        choices: ["present", "absent", "latest"]

    recurse:
        description:
            - When removing a package, also remove its dependencies, provided
              that they are not required by other packages and were not
              explicitly installed by a user.
        required: false
        default: "no"
        choices: ["yes", "no"]
        version_added: "1.3"

    update_cache:
        description:
            - Whether or not to refresh the master package lists. This can be
              run as part of a package installation or as a separate step.
        required: false
        default: "no"
        choices: ["yes", "no"]
'''

EXAMPLES = '''
# Install package foo
- pacman: name=foo state=present

# Upgrade package foo
- pacman: name=foo state=latest update_cache=yes

# Remove packages foo and bar
- pacman: name=foo,bar state=absent

# Recursively remove package baz
- pacman: name=baz state=absent recurse=yes

# Run the equivalent of "pacman -Syy" as a separate step
- pacman: update_cache=yes
'''

import json
import shlex
import os
import re
import sys

PACMAN_PATH = "/usr/bin/pacman"

def get_version(pacman_output):
    """Take pacman -Qi or pacman -Si output and get the Version"""
    lines = pacman_output.split('\n')
    for line in lines:
        if 'Version' in line:
            return line.split(':')[1].strip()
    return None

def query_package(module, name, state="present"):
    """Query the package status in both the local system and the repository. Returns a boolean to indicate if the package is installed, and a second boolean to indicate if the package is up-to-date."""
    if state == "present":
        lcmd = "pacman -Qi %s" % (name)
        lrc, lstdout, lstderr = module.run_command(lcmd, check_rc=False)
        if lrc != 0:
            # package is not installed locally
            return False, False
        
        # get the version installed locally (if any)
        lversion = get_version(lstdout)
        
        rcmd = "pacman -Si %s" % (name)
        rrc, rstdout, rstderr = module.run_command(rcmd, check_rc=False)
        # get the version in the repository
        rversion = get_version(rstdout)

        if rrc == 0:
            # Return True to indicate that the package is installed locally, and the result of the version number comparison
            # to determine if the package is up-to-date.
            return True, (lversion == rversion)

        return False, False


def update_package_db(module):
    cmd = "pacman -Syy"
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        return True
    else:
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
        installed, updated = query_package(module, package)
        if not installed:
            continue

        cmd = "pacman -%s %s --noconfirm" % (args, package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, state, packages, package_files):
    install_c = 0

    for i, package in enumerate(packages):
        # if the package is installed and state == present or state == latest and is up-to-date then skip
        installed, updated = query_package(module, package)
        if installed and (state == 'present' or (state == 'latest' and updated)):
            continue

        if package_files[i]:
            params = '-U %s' % package_files[i]
        else:
            params = '-S %s' % package

        cmd = "pacman %s --noconfirm" % (params)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to install %s" % (package))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already installed")


def check_packages(module, packages, state):
    would_be_changed = []
    for package in packages:
        installed, updated = query_package(module, package)
        if ((state in ["present", "latest"] and not installed) or
                (state == "absent" and installed) or
                (state == "latest" and not updated)):
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
            name         = dict(aliases=['pkg']),
            state        = dict(default='present', choices=['present', 'installed', "latest", 'absent', 'removed']),
            recurse      = dict(default='no', choices=BOOLEANS, type='bool'),
            update_cache = dict(default='no', aliases=['update-cache'], choices=BOOLEANS, type='bool')),
        required_one_of = [['name', 'update_cache']],
        supports_check_mode = True)

    if not os.path.exists(PACMAN_PATH):
        module.fail_json(msg="cannot find pacman, looking for %s" % (PACMAN_PATH))

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    elif p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p["update_cache"] and not module.check_mode:
        update_package_db(module)
        if not p['name']:
            module.exit_json(changed=True, msg='updated the package master lists')

    if p['update_cache'] and module.check_mode and not p['name']:
        module.exit_json(changed=True, msg='Would have updated the package cache')

    if p['name']:
        pkgs = p['name'].split(',')

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

        if p['state'] in ['present', 'latest']:
            install_packages(module, p['state'], pkgs, pkg_files)
        elif p['state'] == 'absent':
            remove_packages(module, pkgs)

# import module snippets
from ansible.module_utils.basic import *
    
main()        
