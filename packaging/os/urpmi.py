#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2013, Philippe Makowski
# Written by Philippe Makowski <philippem@mageia.org> 
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
module: urpmi
short_description: Urpmi manager
description:
  - Manages packages with I(urpmi) (such as for Mageia or Mandriva)
version_added: "1.3.4"
options:
  pkg:
    description:
      - name of package to install, upgrade or remove.
    required: true
    default: null
  state:
    description:
      - Indicates the desired package state
    required: false
    default: present
    choices: [ "absent", "present" ]
  update_cache:
    description:
      - update the package database first C(urpmi.update -a).
    required: false
    default: no
    choices: [ "yes", "no" ]
  no-recommends:
    description:
      - Corresponds to the C(--no-recommends) option for I(urpmi).
    required: false
    default: yes
    choices: [ "yes", "no" ]
  force:
    description:
      - Assume "yes" is the answer to any question urpmi has to ask.
        Corresponds to the C(--force) option for I(urpmi).
    required: false
    default: yes
    choices: [ "yes", "no" ]
author: "Philippe Makowski (@pmakowski)"
notes:  []
'''

EXAMPLES = '''
# install package foo
- urpmi: pkg=foo state=present
# remove package foo
- urpmi: pkg=foo state=absent
# description: remove packages foo and bar 
- urpmi: pkg=foo,bar state=absent
# description: update the package database (urpmi.update -a -q) and install bar (bar will be the updated if a newer version exists) 
- urpmi: name=bar, state=present, update_cache=yes     
'''


import shlex
import os
import sys

URPMI_PATH = '/usr/sbin/urpmi'
URPME_PATH = '/usr/sbin/urpme'

def query_package(module, name):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    cmd = "rpm -q %s" % (name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return True
    else:
        return False

def query_package_provides(module, name):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    cmd = "rpm -q --provides %s" % (name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    return rc == 0


def update_package_db(module):
    cmd = "urpmi.update -a -q"
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="could not update package db")
         

def remove_packages(module, packages):
    
    remove_c = 0
    # Using a for loop incase of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package):
            continue

        cmd = "%s --auto %s" % (URPME_PATH, package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))
    
        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pkgspec, force=True, no_recommends=True):

    packages = ""
    for package in pkgspec:
        if not query_package_provides(module, package):
            packages += "'%s' " % package

    if len(packages) != 0:
        if no_recommends:
            no_recommends_yes = '--no-recommends'
        else:
            no_recommends_yes = ''

        if force:
            force_yes = '--force'
        else:
            force_yes = ''

        cmd = ("%s --auto %s --quiet %s %s" % (URPMI_PATH, force_yes, no_recommends_yes, packages))

        rc, out, err = module.run_command(cmd)

        installed = True
        for packages in pkgspec:
            if not query_package_provides(module, package):
                installed = False

        # urpmi always have 0 for exit code if --force is used
        if rc or not installed:
            module.fail_json(msg="'urpmi %s' failed: %s" % (packages, err))
        else:
            module.exit_json(changed=True, msg="%s present(s)" % packages)
    else:
        module.exit_json(changed=False)


def main():
    module = AnsibleModule(
            argument_spec     = dict(
                state         = dict(default='installed', choices=['installed', 'removed', 'absent', 'present']),
                update_cache  = dict(default=False, aliases=['update-cache'], type='bool'),
                force         = dict(default=True, type='bool'),
                no_recommends = dict(default=True, aliases=['no-recommends'], type='bool'),
                package       = dict(aliases=['pkg', 'name'], required=True)))
                

    if not os.path.exists(URPMI_PATH):
        module.fail_json(msg="cannot find urpmi, looking for %s" % (URPMI_PATH))

    p = module.params

    force_yes = p['force']
    no_recommends_yes = p['no_recommends']

    if p['update_cache']:
        update_package_db(module)

    packages = p['package'].split(',')

    if p['state'] in [ 'installed', 'present' ]:
        install_packages(module, packages, force_yes, no_recommends_yes)

    elif p['state'] in [ 'removed', 'absent' ]:
        remove_packages(module, packages)

# import module snippets
from ansible.module_utils.basic import *
    
main()        
