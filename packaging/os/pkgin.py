#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2013 Shaun Zinck <shaun.zinck at gmail.com>
# Copyright (c) 2015 Lawrence Leonard Gilbert <larry@L2G.to>
#
# Written by Shaun Zinck
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
short_description: Package manager for SmartOS, NetBSD, et al.
description:
    - "The standard package manager for SmartOS, but also usable on NetBSD
      or any OS that uses C(pkgsrc).  (Home: U(http://pkgin.net/))"
version_added: "1.0"
author: Shaun Zinck, Larry Gilbert
notes:
    - "Known bug with pkgin < 0.8.0: if a package is removed and another
      package depends on it, the other package will be silently removed as
      well.  New to Ansible 1.9: check-mode support."
options:
    name:
        description:
            - Name of package to install/remove;
            - multiple names may be given, separated by commas
        required: true
    state:
        description:
            - Intended state of the package
        choices: [ 'present', 'absent' ]
        required: false
        default: present
'''

EXAMPLES = '''
# install package foo
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

def query_package(module, pkgin_path, name):
    """Search for the package by name.

    Possible return values:
    * "present"  - installed, no upgrade needed
    * "outdated" - installed, but can be upgraded
    * False      - not installed or not found
    """

    # Use "pkgin search" to find the package. The regular expression will
    # only match on the complete name.
    rc, out, err = module.run_command("%s search \"^%s$\"" % (pkgin_path, name))

    # rc will not be 0 unless the search was a success
    if rc == 0:

        # Get first line
        line = out.split('\n')[0]

        # Break up line at spaces.  The first part will be the package with its
        # version (e.g. 'gcc47-libs-4.7.2nb4'), and the second will be the state
        # of the package:
        #     ''  - not installed
        #     '<' - installed but out of date
        #     '=' - installed and up to date
        #     '>' - installed but newer than the repository version
        pkgname_with_version, raw_state = out.split(' ')[0:2]

        # Strip version
        # (results in sth like 'gcc47-libs')
        pkgname_without_version = '-'.join(pkgname_with_version.split('-')[:-1])

        if name != pkgname_without_version:
            return False
        # no fall-through

        # The package was found; now return its state
        if raw_state == '<':
            return 'outdated'
        elif raw_state == '=' or raw_state == '>':
            return 'present'
        else:
            return False


def format_action_message(module, action, count):
    vars = { "actioned": action,
             "count":    count }

    if module.check_mode:
        message = "would have %(actioned)s %(count)d package" % vars
    else:
        message = "%(actioned)s %(count)d package" % vars

    if count == 1:
        return message
    else:
        return message + "s"


def format_pkgin_command(module, pkgin_path, command, package):
    vars = { "pkgin":   pkgin_path,
             "command": command,
             "package": package }

    if module.check_mode:
        return "%(pkgin)s -n %(command)s %(package)s" % vars
    else:
        return "%(pkgin)s -y %(command)s %(package)s" % vars


def remove_packages(module, pkgin_path, packages):

    remove_c = 0

    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, pkgin_path, package):
            continue

        rc, out, err = module.run_command(
            format_pkgin_command(module, pkgin_path, "remove", package))

        if not module.check_mode and query_package(module, pkgin_path, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:
        module.exit_json(changed=True, msg=format_action_message(module, "removed", remove_c))

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pkgin_path, packages):

    install_c = 0

    for package in packages:
        if query_package(module, pkgin_path, package):
            continue

        rc, out, err = module.run_command(
            format_pkgin_command(module, pkgin_path, "install", package))

        if not module.check_mode and not query_package(module, pkgin_path, package):
            module.fail_json(msg="failed to install %s: %s" % (package, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg=format_action_message(module, "installed", install_c))

    module.exit_json(changed=False, msg="package(s) already present")



def main():
    module = AnsibleModule(
            argument_spec    = dict(
                state        = dict(default="present", choices=["present","absent"]),
                name         = dict(aliases=["pkg"], required=True)),
            supports_check_mode = True)

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
