#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, berenddeboer
# Written by berenddeboer <berend@pobox.com>
# Based on pkgng module written by bleader <bleader at ratonland.org>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: portinstall
short_description: Installing packages from FreeBSD's ports system
description:
    - Manage packages for FreeBSD using 'portinstall'.
version_added: "1.3"
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
    use_packages:
        description:
            - use packages instead of ports whenever available
        type: bool
        required: false
        default: yes
author: "berenddeboer (@berenddeboer)"
'''

EXAMPLES = '''
# Install package foo
- portinstall:
    name: foo
    state: present

# Install package security/cyrus-sasl2-saslauthd
- portinstall:
    name: security/cyrus-sasl2-saslauthd
    state: present

# Remove packages foo and bar
- portinstall:
    name: foo,bar
    state: absent
'''

import os
import re
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import shlex_quote


def query_package(module, name):

    pkg_info_path = module.get_bin_path('pkg_info', False)

    # Assume that if we have pkg_info, we haven't upgraded to pkgng
    if pkg_info_path:
        pkgng = False
        pkg_glob_path = module.get_bin_path('pkg_glob', True)
        rc, out, err = module.run_command("%s -e `pkg_glob %s`" % (pkg_info_path, shlex_quote(name)), use_unsafe_shell=True)
    else:
        pkgng = True
        pkg_info_path = module.get_bin_path('pkg', True)
        pkg_info_path = pkg_info_path + " info"
        rc, out, err = module.run_command("%s %s" % (pkg_info_path, name))

    found = rc == 0

    if not found:
        # databases/mysql55-client installs as mysql-client, so try solving
        # that the ugly way. Pity FreeBSD doesn't have a fool proof way of checking
        # some package is installed
        name_without_digits = re.sub('[0-9]', '', name)
        if name != name_without_digits:
            if pkgng:
                rc, out, err = module.run_command("%s %s" % (pkg_info_path, name_without_digits))
            else:
                rc, out, err = module.run_command("%s %s" % (pkg_info_path, name_without_digits))

        found = rc == 0

    return found


def matching_packages(module, name):

    ports_glob_path = module.get_bin_path('ports_glob', True)
    rc, out, err = module.run_command("%s %s" % (ports_glob_path, name))
    # counts the number of packages found
    occurrences = out.count('\n')
    if occurrences == 0:
        name_without_digits = re.sub('[0-9]', '', name)
        if name != name_without_digits:
            rc, out, err = module.run_command("%s %s" % (ports_glob_path, name_without_digits))
            occurrences = out.count('\n')
    return occurrences


def remove_packages(module, packages):

    remove_c = 0
    pkg_glob_path = module.get_bin_path('pkg_glob', True)

    # If pkg_delete not found, we assume pkgng
    pkg_delete_path = module.get_bin_path('pkg_delete', False)
    if not pkg_delete_path:
        pkg_delete_path = module.get_bin_path('pkg', True)
        pkg_delete_path = pkg_delete_path + " delete -y"

    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package):
            continue

        rc, out, err = module.run_command("%s `%s %s`" % (pkg_delete_path, pkg_glob_path, shlex_quote(package)), use_unsafe_shell=True)

        if query_package(module, package):
            name_without_digits = re.sub('[0-9]', '', package)
            rc, out, err = module.run_command("%s `%s %s`" % (pkg_delete_path, pkg_glob_path,
                                                              shlex_quote(name_without_digits)),
                                              use_unsafe_shell=True)
            if query_package(module, package):
                module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, packages, use_packages):

    install_c = 0

    # If portinstall not found, automagically install
    portinstall_path = module.get_bin_path('portinstall', False)
    if not portinstall_path:
        pkg_path = module.get_bin_path('pkg', False)
        if pkg_path:
            module.run_command("pkg install -y portupgrade")
        portinstall_path = module.get_bin_path('portinstall', True)

    if use_packages:
        portinstall_params = "--use-packages"
    else:
        portinstall_params = ""

    for package in packages:
        if query_package(module, package):
            continue

        # TODO: check how many match
        matches = matching_packages(module, package)
        if matches == 1:
            rc, out, err = module.run_command("%s --batch %s %s" % (portinstall_path, portinstall_params, package))
            if not query_package(module, package):
                module.fail_json(msg="failed to install %s: %s" % (package, out))
        elif matches == 0:
            module.fail_json(msg="no matches for package %s" % (package))
        else:
            module.fail_json(msg="%s matches found for package name %s" % (matches, package))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="present %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=["present", "absent"]),
            name=dict(aliases=["pkg"], required=True),
            use_packages=dict(type='bool', default='yes')))

    p = module.params

    pkgs = p["name"].split(",")

    if p["state"] == "present":
        install_packages(module, pkgs, p["use_packages"])

    elif p["state"] == "absent":
        remove_packages(module, pkgs)


if __name__ == '__main__':
    main()
