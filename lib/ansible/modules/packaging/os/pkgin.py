#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2013 Shaun Zinck <shaun.zinck at gmail.com>
# Copyright (c) 2015 Lawrence Leonard Gilbert <larry@L2G.to>
# Copyright (c) 2016 Jasper Lievisse Adriaanse <j at jasper.la>
#
# Written by Shaun Zinck
# Based on pacman module written by Afterburn <http://github.com/afterburn>
#  that was based on apt module written by Matthew Williams <matthew@flowroute.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pkgin
short_description: Package manager for SmartOS, NetBSD, et al.
description:
    - "The standard package manager for SmartOS, but also usable on NetBSD
      or any OS that uses C(pkgsrc).  (Home: U(http://pkgin.net/))"
version_added: "1.0"
author:
    - "Larry Gilbert (L2G)"
    - "Shaun Zinck (@szinck)"
    - "Jasper Lievisse Adriaanse (@jasperla)"
notes:
    - "Known bug with pkgin < 0.8.0: if a package is removed and another
      package depends on it, the other package will be silently removed as
      well.  New to Ansible 1.9: check-mode support."
options:
    name:
        description:
            - Name of package to install/remove;
            - multiple names may be given, separated by commas
        required: false
        default: null
    state:
        description:
            - Intended state of the package
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    update_cache:
        description:
          - Update repository database. Can be run with other steps or on it's own.
        required: false
        default: no
        choices: [ "yes", "no" ]
        version_added: "2.1"
    upgrade:
        description:
          - Upgrade main packages to their newer versions
        required: false
        default: no
        choices: [ "yes", "no" ]
        version_added: "2.1"
    full_upgrade:
        description:
          - Upgrade all packages to their newer versions
        required: false
        default: no
        choices: [ "yes", "no" ]
        version_added: "2.1"
    clean:
        description:
          - Clean packages cache
        required: false
        default: no
        choices: [ "yes", "no" ]
        version_added: "2.1"
    force:
        description:
          - Force package reinstall
        required: false
        default: no
        choices: [ "yes", "no" ]
        version_added: "2.1"
'''

EXAMPLES = '''
# install package foo
- pkgin:
    name: foo
    state: present

# Update database and install "foo" package
- pkgin:
    name: foo
    update_cache: yes

# remove package foo
- pkgin:
    name: foo
    state: absent

# remove packages foo and bar
- pkgin:
    name: foo,bar
    state: absent

# Update repositories as a separate step
- pkgin:
    update_cache: yes

# Upgrade main packages (equivalent to C(pkgin upgrade))
- pkgin:
    upgrade: yes

# Upgrade all packages (equivalent to C(pkgin full-upgrade))
- pkgin:
    full_upgrade: yes

# Force-upgrade all packages (equivalent to C(pkgin -F full-upgrade))
- pkgin:
    full_upgrade: yes
    force: yes

# clean packages cache (equivalent to C(pkgin clean))
- pkgin:
    clean: yes
'''


import re


def query_package(module, name):
    """Search for the package by name.

    Possible return values:
    * "present"  - installed, no upgrade needed
    * "outdated" - installed, but can be upgraded
    * False      - not installed or not found
    """

    # test whether '-p' (parsable) flag is supported.
    rc, out, err = module.run_command("%s -p -v" % PKGIN_PATH)

    if rc == 0:
        pflag = '-p'
        splitchar = ';'
    else:
        pflag = ''
        splitchar = ' '

    # Use "pkgin search" to find the package. The regular expression will
    # only match on the complete name.
    rc, out, err = module.run_command("%s %s search \"^%s$\"" % (PKGIN_PATH, pflag, name))

    # rc will not be 0 unless the search was a success
    if rc == 0:

        # Search results may contain more than one line (e.g., 'emacs'), so iterate
        # through each line to see if we have a match.
        packages = out.split('\n')

        for package in packages:

            # Break up line at spaces.  The first part will be the package with its
            # version (e.g. 'gcc47-libs-4.7.2nb4'), and the second will be the state
            # of the package:
            #     ''  - not installed
            #     '<' - installed but out of date
            #     '=' - installed and up to date
            #     '>' - installed but newer than the repository version
            pkgname_with_version, raw_state = package.split(splitchar)[0:2]

            # Search for package, stripping version
            # (results in sth like 'gcc47-libs' or 'emacs24-nox11')
            pkg_search_obj = re.search(r'^(.*?)\-[0-9][0-9.]*(nb[0-9]+)*', pkgname_with_version, re.M)

            # Do not proceed unless we have a match
            if not pkg_search_obj:
                continue

            # Grab matched string
            pkgname_without_version = pkg_search_obj.group(1)

            if name != pkgname_without_version:
                continue

            # The package was found; now return its state
            if raw_state == '<':
                return 'outdated'
            elif raw_state == '=' or raw_state == '>':
                return 'present'
            else:
                return False
            # no fall-through

        # No packages were matched, so return False
        return False


def format_action_message(module, action, count):
    vars = {"actioned": action,
            "count": count}

    if module.check_mode:
        message = "would have %(actioned)s %(count)d package" % vars
    else:
        message = "%(actioned)s %(count)d package" % vars

    if count == 1:
        return message
    else:
        return message + "s"


def format_pkgin_command(module, command, package=None):
    # Not all commands take a package argument, so cover this up by passing
    # an empty string. Some commands (e.g. 'update') will ignore extra
    # arguments, however this behaviour cannot be relied on for others.
    if package is None:
        package = ""

    if module.params["force"]:
        force = "-F"
    else:
        force = ""

    vars = {"pkgin": PKGIN_PATH,
            "command": command,
            "package": package,
            "force": force}

    if module.check_mode:
        return "%(pkgin)s -n %(command)s %(package)s" % vars
    else:
        return "%(pkgin)s -y %(force)s %(command)s %(package)s" % vars


def remove_packages(module, packages):

    remove_c = 0

    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, package):
            continue

        rc, out, err = module.run_command(
            format_pkgin_command(module, "remove", package))

        if not module.check_mode and query_package(module, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:
        module.exit_json(changed=True, msg=format_action_message(module, "removed", remove_c))

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, packages):

    install_c = 0

    for package in packages:
        if query_package(module, package):
            continue

        rc, out, err = module.run_command(
            format_pkgin_command(module, "install", package))

        if not module.check_mode and not query_package(module, package):
            module.fail_json(msg="failed to install %s: %s" % (package, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg=format_action_message(module, "installed", install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def update_package_db(module):
    rc, out, err = module.run_command(
        format_pkgin_command(module, "update"))

    if rc == 0:
        if re.search('database for.*is up-to-date\n$', out):
            return False, "datebase is up-to-date"
        else:
            return True, "updated repository database"
    else:
        module.fail_json(msg="could not update package db")


def do_upgrade_packages(module, full=False):
    if full:
        cmd = "full-upgrade"
    else:
        cmd = "upgrade"

    rc, out, err = module.run_command(
        format_pkgin_command(module, cmd))

    if rc == 0:
        if re.search('^nothing to do.\n$', out):
            module.exit_json(changed=False, msg="nothing left to upgrade")
    else:
        module.fail_json(msg="could not %s packages" % cmd)


def upgrade_packages(module):
    do_upgrade_packages(module)


def full_upgrade_packages(module):
    do_upgrade_packages(module, True)


def clean_cache(module):
    rc, out, err = module.run_command(
        format_pkgin_command(module, "clean"))

    if rc == 0:
        # There's no indication if 'clean' actually removed anything,
        # so assume it did.
        module.exit_json(changed=True, msg="cleaned caches")
    else:
        module.fail_json(msg="could not clean package cache")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="present", choices=["present", "absent"]),
            name=dict(aliases=["pkg"], type='list'),
            update_cache=dict(default='no', type='bool'),
            upgrade=dict(default='no', type='bool'),
            full_upgrade=dict(default='no', type='bool'),
            clean=dict(default='no', type='bool'),
            force=dict(default='no', type='bool')),
        required_one_of=[['name', 'update_cache', 'upgrade', 'full_upgrade', 'clean']],
        supports_check_mode=True)

    global PKGIN_PATH
    PKGIN_PATH = module.get_bin_path('pkgin', True, ['/opt/local/bin'])

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    p = module.params

    if p["update_cache"]:
        c, msg = update_package_db(module)
        if not (p['name'] or p["upgrade"] or p["full_upgrade"]):
            module.exit_json(changed=c, msg=msg)

    if p["upgrade"]:
        upgrade_packages(module)
        if not p['name']:
            module.exit_json(changed=True, msg='upgraded packages')

    if p["full_upgrade"]:
        full_upgrade_packages(module)
        if not p['name']:
            module.exit_json(changed=True, msg='upgraded all packages')

    if p["clean"]:
        clean_cache(module)
        if not p['name']:
            module.exit_json(changed=True, msg='cleaned caches')

    pkgs = p["name"]

    if p["state"] == "present":
        install_packages(module, pkgs)

    elif p["state"] == "absent":
        remove_packages(module, pkgs)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
