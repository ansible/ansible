#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Shaun Zinck
# Written by Shaun Zinck <shaun.zinck at gmail.com>
# Based on pacman module written by Afterburn <http://github.com/afterburn>
#  that was based on apt module written by Matthew Williams <matthew@flowroute.com>
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
module: pkgin
short_description: Package manager for SmartOS
description:
    - Manages SmartOS packages
version_added: "1.0"
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
author: Shaun Zinck
notes:  []
'''

EXAMPLES = '''
# install package foo"
- pkgin: name=foo state=present

# remove package foo
- pkgin: name=foo state=absent

# remove packages foo and bar
- pkgin: name=foo,bar state=absent
'''


import json
import shlex
import os
import sys
import pipes

def query_package(module, pkgin_path, name, state="present"):

    if state == "present":

        rc, out, err = module.run_command("%s -y list | grep ^%s" % (pipes.quote(pkgin_path), pipes.quote(name)), use_unsafe_shell=True)

        if rc == 0:
            # At least one package with a package name that starts with ``name``
            # is installed.  For some cases this is not sufficient to determine
            # wether the queried package is installed.
            #
            # E.g. for ``name='gcc47'``, ``gcc47`` not being installed, but
            # ``gcc47-libs`` being installed, ``out`` would be:
            #
            #   gcc47-libs-4.7.2nb4  The GNU Compiler Collection (GCC) support shared libraries.
            #
            # Multiline output is also possible, for example with the same query
            # and bot ``gcc47`` and ``gcc47-libs`` being installed:
            #
            #   gcc47-libs-4.7.2nb4   The GNU Compiler Collection (GCC) support shared libraries.
            #   gcc47-4.7.2nb3       The GNU Compiler Collection (GCC) - 4.7 Release Series

            # Loop over lines in ``out``
            for line in out.split('\n'):

                # Strip description
                # (results in sth. like 'gcc47-libs-4.7.2nb4')
                pkgname_with_version = out.split(' ')[0]

                # Strip version
                # (results in sth like 'gcc47-libs')
                pkgname_without_version = '-'.join(pkgname_with_version.split('-')[:-1])

                if name == pkgname_without_version:
                    return True

        return False


def remove_packages(module, pkgin_path, packages):

    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, pkgin_path, package):
            continue

        rc, out, err = module.run_command("%s -y remove %s" % (pkgin_path, package))

        if query_package(module, pkgin_path, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pkgin_path, packages):

    install_c = 0

    for package in packages:
        if query_package(module, pkgin_path, package):
            continue

        rc, out, err = module.run_command("%s -y install %s" % (pkgin_path, package))

        if not query_package(module, pkgin_path, package):
            module.fail_json(msg="failed to install %s: %s" % (package, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="present %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")



def main():
    module = AnsibleModule(
            argument_spec    = dict(
                state        = dict(default="present", choices=["present","absent"]),
                name         = dict(aliases=["pkg"], required=True)))

    pkgin_path = module.get_bin_path('pkgin', True, ['/opt/local/bin'])

    p = module.params

    pkgs = p["name"].split(",")

    if p["state"] == "present":
        install_packages(module, pkgin_path, pkgs)

    elif p["state"] == "absent":
        remove_packages(module, pkgin_path, pkgs)

# import module snippets
from ansible.module_utils.basic import *

main()
