#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Philippe Makowski
# Written by Philippe Makowski <philippem@mageia.org>
# Based on apt module written by Matthew Williams <matthew@flowroute.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
  name:
    description:
      - A list of package names to install, upgrade or remove.
    required: yes
    version_added: "2.6"
    aliases: [ package, pkg ]
  state:
    description:
      - Indicates the desired package state.
    choices: [ absent, present ]
    default: present
  update_cache:
    description:
      - Update the package database first C(urpmi.update -a).
    type: bool
    default: 'no'
  no-recommends:
    description:
      - Corresponds to the C(--no-recommends) option for I(urpmi).
    type: bool
    default: 'yes'
    aliases: ['no-recommends']
  force:
    description:
      - Assume "yes" is the answer to any question urpmi has to ask.
        Corresponds to the C(--force) option for I(urpmi).
    type: bool
    default: 'yes'
  root:
    description:
      - Specifies an alternative install root, relative to which all packages will be installed.
        Corresponds to the C(--root) option for I(urpmi).
    default: /
    version_added: "2.4"
    aliases: [ installroot ]
author:
- Philippe Makowski (@pmakowski)
'''

EXAMPLES = '''
- name: Install package foo
  urpmi:
    pkg: foo
    state: present

- name: Remove package foo
  urpmi:
    pkg: foo
    state: absent

- name: Remove packages foo and bar
  urpmi:
    pkg: foo,bar
    state: absent

- name: Update the package database (urpmi.update -a -q) and install bar (bar will be the updated if a newer version exists)
- urpmi:
    name: bar
    state: present
    update_cache: yes
'''


import os
import shlex
import sys

from ansible.module_utils.basic import AnsibleModule


def query_package(module, name, root):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    rpm_path = module.get_bin_path("rpm", True)
    cmd = "%s -q %s %s" % (rpm_path, name, root_option(root))
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return True
    else:
        return False


def query_package_provides(module, name, root):
    # rpm -q returns 0 if the package is installed,
    # 1 if it is not installed
    rpm_path = module.get_bin_path("rpm", True)
    cmd = "%s -q --whatprovides %s %s" % (rpm_path, name, root_option(root))
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    return rc == 0


def update_package_db(module):

    urpmiupdate_path = module.get_bin_path("urpmi.update", True)
    cmd = "%s -a -q" % (urpmiupdate_path,)
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

        urpme_path = module.get_bin_path("urpme", True)
        cmd = "%s --auto %s %s" % (urpme_path, root_option(root), package)
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

        urpmi_path = module.get_bin_path("urpmi", True)
        cmd = ("%s --auto %s --quiet %s %s %s" % (urpmi_path, force_yes,
                                                  no_recommends_yes,
                                                  root_option(root),
                                                  packages))

        rc, out, err = module.run_command(cmd)

        for package in pkgspec:
            if not query_package_provides(module, package, root):
                module.fail_json(msg="'urpmi %s' failed: %s" % (package, err))

        # urpmi always have 0 for exit code if --force is used
        if rc:
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
        argument_spec=dict(
            state=dict(type='str', default='installed',
                       choices=['absent', 'installed', 'present', 'removed']),
            update_cache=dict(type='bool', default=False, aliases=['update-cache']),
            force=dict(type='bool', default=True),
            no_recommends=dict(type='bool', default=True, aliases=['no-recommends']),
            name=dict(type='list', required=True, aliases=['package', 'pkg']),
            root=dict(type='str', aliases=['installroot']),
        ),
    )

    p = module.params

    if p['update_cache']:
        update_package_db(module)

    if p['state'] in ['installed', 'present']:
        install_packages(module, p['name'], p['root'], p['force'], p['no_recommends'])

    elif p['state'] in ['removed', 'absent']:
        remove_packages(module, p['name'], p['root'])


if __name__ == '__main__':
    main()
