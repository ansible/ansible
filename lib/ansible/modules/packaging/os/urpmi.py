#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2013, Philippe Makowski
# Written by Philippe Makowski <philippem@mageia.org>
# Based on apt module written by Matthew Williams <matthew@flowroute.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  root:
    description:
      - Specifies an alternative install root, relative to which all packages will be installed.
        Corresponds to the C(--root) option for I(urpmi).
    required: false
    default: "/"
    version_added: "2.4"
    aliases: [ "installroot" ]
author: "Philippe Makowski (@pmakowski)"
notes:  []
'''

EXAMPLES = '''
# install package foo
- urpmi:
    pkg: foo
    state: present

# remove package foo
- urpmi:
    pkg: foo
    state: absent

# description: remove packages foo and bar
- urpmi:
    pkg: foo,bar
    state: absent

# description: update the package database (urpmi.update -a -q) and install bar (bar will be the updated if a newer version exists)
- urpmi:
    name: bar
    state: present
    update_cache: yes
'''


import shlex
import os
import sys

URPMI_PATH = '/usr/sbin/urpmi'
URPME_PATH = '/usr/sbin/urpme'

def query_package(module, name, root):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    cmd = "rpm -q %s %s" % (name, root_option(root))
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return True
    else:
        return False

def query_package_provides(module, name, root):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    cmd = "rpm -q --provides %s %s" % (name, root_option(root))
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    return rc == 0


def update_package_db(module):
    cmd = "urpmi.update -a -q"
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="could not update package db")


def remove_packages(module, packages, root):

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package, root):
            continue

        cmd = "%s --auto %s %s" % (URPME_PATH, root_option(root), package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pkgspec, root, force=True, no_recommends=True):

    packages = ""
    for package in pkgspec:
        if not query_package_provides(module, package, root):
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

        cmd = ("%s --auto %s --quiet %s %s %s" % (URPMI_PATH, force_yes, no_recommends_yes, root_option(root), packages))

        rc, out, err = module.run_command(cmd)

        installed = True
        for packages in pkgspec:
            if not query_package_provides(module, package, root):
                installed = False

        # urpmi always have 0 for exit code if --force is used
        if rc or not installed:
            module.fail_json(msg="'urpmi %s' failed: %s" % (packages, err))
        else:
            module.exit_json(changed=True, msg="%s present(s)" % packages)
    else:
        module.exit_json(changed=False)

def root_option(root):
    if (root):
        return "--root=%s" % (root)
    else:
        return ""

def main():
    module = AnsibleModule(
        argument_spec     = dict(
            state         = dict(default='installed', choices=['installed', 'removed', 'absent', 'present']),
            update_cache  = dict(default=False, aliases=['update-cache'], type='bool'),
            force         = dict(default=True, type='bool'),
            no_recommends = dict(default=True, aliases=['no-recommends'], type='bool'),
            package       = dict(aliases=['pkg', 'name'], required=True),
            root          = dict(aliases=['installroot'])))


    if not os.path.exists(URPMI_PATH):
        module.fail_json(msg="cannot find urpmi, looking for %s" % (URPMI_PATH))

    p = module.params

    force_yes = p['force']
    no_recommends_yes = p['no_recommends']
    root = p['root']

    if p['update_cache']:
        update_package_db(module)

    packages = p['package'].split(',')

    if p['state'] in [ 'installed', 'present' ]:
        install_packages(module, packages, root, force_yes, no_recommends_yes)

    elif p['state'] in [ 'removed', 'absent' ]:
        remove_packages(module, packages, root)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
