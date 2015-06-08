#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2012, Afterburn <http://github.com/afterburn>
# (c) 2013, Aaron Bull Schaefer <aaron@elasticdog.com>
# (c) 2015, Jonathan Lestrelin <jonathan.lestrelin@gmail.com>
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
module: pear
short_description: Manage pear/pecl packages
description:
    - Manage PHP packages with the pear package manager.
version_added: 2.0
author:
    - "'jonathan.lestrelin' <jonathan.lestrelin@gmail.com>"
options:
    name:
        description:
            - Name of the package to install, upgrade, or remove.
        required: true

    state:
        description:
            - Desired state of the package.
        required: false
        default: "present"
        choices: ["present", "absent", "latest"]
'''

EXAMPLES = '''
# Install pear package
- pear: name=Net_URL2 state=present

# Install pecl package
- pear: name=pecl/json_post state=present

# Upgrade package
- pear: name=Net_URL2 state=latest

# Remove packages
- pear: name=Net_URL2,pecl/json_post state=absent
'''

import os

def get_local_version(pear_output):
    """Take pear remoteinfo output and get the installed version"""
    lines = pear_output.split('\n')
    for line in lines:
        if 'Installed ' in line:
            installed = line.rsplit(None, 1)[-1].strip()
            if installed == '-': continue
            return installed
    return None

def get_repository_version(pear_output):
    """Take pear remote-info output and get the latest version"""
    lines = pear_output.split('\n')
    for line in lines:
        if 'Latest ' in line:
            return line.rsplit(None, 1)[-1].strip()
    return None

def query_package(module, name, state="present"):
    """Query the package status in both the local system and the repository.
    Returns a boolean to indicate if the package is installed,
    and a second boolean to indicate if the package is up-to-date."""
    if state == "present":
        lcmd = "pear info %s" % (name)
        lrc, lstdout, lstderr = module.run_command(lcmd, check_rc=False)
        if lrc != 0:
            # package is not installed locally
            return False, False

        rcmd = "pear remote-info %s" % (name)
        rrc, rstdout, rstderr = module.run_command(rcmd, check_rc=False)

        # get the version installed locally (if any)
        lversion = get_local_version(rstdout)

        # get the version in the repository
        rversion = get_repository_version(rstdout)

        if rrc == 0:
            # Return True to indicate that the package is installed locally,
            # and the result of the version number comparison
            # to determine if the package is up-to-date.
            return True, (lversion == rversion)

        return False, False


def remove_packages(module, packages):
    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        installed, updated = query_package(module, package)
        if not installed:
            continue

        cmd = "pear uninstall %s" % (package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, state, packages):
    install_c = 0

    for i, package in enumerate(packages):
        # if the package is installed and state == present
        # or state == latest and is up-to-date then skip
        installed, updated = query_package(module, package)
        if installed and (state == 'present' or (state == 'latest' and updated)):
            continue

        if state == 'present':
            command = 'install'

        if state == 'latest':
            command = 'upgrade'

        cmd = "pear %s %s" % (command, package)
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


def exe_exists(program):
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, program)
        if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
            return True

    return False


def main():
    module = AnsibleModule(
        argument_spec    = dict(
            name         = dict(aliases=['pkg']),
            state        = dict(default='present', choices=['present', 'installed', "latest", 'absent', 'removed'])),
        required_one_of = [['name']],
        supports_check_mode = True)

    if not exe_exists("pear"):
        module.fail_json(msg="cannot find pear executable in PATH")

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    elif p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p['name']:
        pkgs = p['name'].split(',')

        pkg_files = []
        for i, pkg in enumerate(pkgs):
            pkg_files.append(None)

        if module.check_mode:
            check_packages(module, pkgs, p['state'])

        if p['state'] in ['present', 'latest']:
            install_packages(module, p['state'], pkgs)
        elif p['state'] == 'absent':
            remove_packages(module, pkgs)

# import module snippets
from ansible.module_utils.basic import *

main()
