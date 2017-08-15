#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2012, Afterburn <http://github.com/afterburn>
# (c) 2013, Aaron Bull Schaefer <aaron@elasticdog.com>
# (c) 2015, Indrajit Raychaudhuri <irc+code@indrajit.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pacman
short_description: Manage packages with I(pacman)
description:
    - Manage packages with the I(pacman) package manager, which is used by
      Arch Linux and its variants.
version_added: "1.0"
author:
    - "Indrajit Raychaudhuri (@indrajitr)"
    - "'Aaron Bull Schaefer (@elasticdog)' <aaron@elasticdog.com>"
    - "Afterburn"
notes: []
requirements: []
options:
    name:
        description:
            - Name of the package to install, upgrade, or remove.
        required: false
        default: null
        aliases: [ 'pkg', 'package' ]

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
        default: no
        choices: ["yes", "no"]
        version_added: "1.3"

    force:
        description:
            - When removing package - force remove package, without any
              checks. When update_cache - force redownload repo
              databases.
        required: false
        default: no
        choices: ["yes", "no"]
        version_added: "2.0"

    update_cache:
        description:
            - Whether or not to refresh the master package lists. This can be
              run as part of a package installation or as a separate step.
        required: false
        default: no
        choices: ["yes", "no"]
        aliases: [ 'update-cache' ]

    upgrade:
        description:
            - Whether or not to upgrade whole system
        required: false
        default: no
        choices: ["yes", "no"]
        version_added: "2.0"
'''

RETURN = '''
packages:
    description: a list of packages that have been changed
    returned: when upgrade is set to yes
    type: list
    sample: ['package', 'other-package']
'''

EXAMPLES = '''
# Install package foo
- pacman:
    name: foo
    state: present

# Upgrade package foo
- pacman:
    name: foo
    state: latest
    update_cache: yes

# Remove packages foo and bar
- pacman:
    name: foo,bar
    state: absent

# Recursively remove package baz
- pacman:
    name: baz
    state: absent
    recurse: yes

# Run the equivalent of "pacman -Sy" as a separate step
- pacman:
    update_cache: yes

# Run the equivalent of "pacman -Su" as a separate step
- pacman:
    upgrade: yes

# Run the equivalent of "pacman -Syu" as a separate step
- pacman:
    update_cache: yes
    upgrade: yes

# Run the equivalent of "pacman -Rdd", force remove package baz
- pacman:
    name: baz
    state: absent
    force: yes
'''

import re

def get_version(pacman_output):
    """Take pacman -Qi or pacman -Si output and get the Version"""
    lines = pacman_output.split('\n')
    for line in lines:
        if 'Version' in line:
            return line.split(':')[1].strip()
    return None

def query_package(module, pacman_path, name, state="present"):
    """Query the package status in both the local system and the repository. Returns a boolean to indicate if the package is installed, a second
    boolean to indicate if the package is up-to-date and a third boolean to indicate whether online information were available
    """
    if state == "present":
        lcmd = "%s -Qi %s" % (pacman_path, name)
        lrc, lstdout, lstderr = module.run_command(lcmd, check_rc=False)
        if lrc != 0:
            # package is not installed locally
            return False, False, False

        # get the version installed locally (if any)
        lversion = get_version(lstdout)

        rcmd = "%s -Si %s" % (pacman_path, name)
        rrc, rstdout, rstderr = module.run_command(rcmd, check_rc=False)
        # get the version in the repository
        rversion = get_version(rstdout)

        if rrc == 0:
            # Return True to indicate that the package is installed locally, and the result of the version number comparison
            # to determine if the package is up-to-date.
            return True, (lversion == rversion), False

    # package is installed but cannot fetch remote Version. Last True stands for the error
        return True, True, True


def update_package_db(module, pacman_path):
    if module.params["force"]:
        args = "Syy"
    else:
        args = "Sy"

    cmd = "%s -%s" % (pacman_path, args)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        return True
    else:
        module.fail_json(msg="could not update package db")

def upgrade(module, pacman_path):
    cmdupgrade = "%s -Suq --noconfirm" % (pacman_path)
    cmdneedrefresh = "%s -Qu" % (pacman_path)
    rc, stdout, stderr = module.run_command(cmdneedrefresh, check_rc=False)
    data = stdout.split('\n')
    data.remove('')
    packages = []
    diff = {
        'before': '',
        'after': '',
    }

    if rc == 0:
        regex = re.compile('([\w-]+) ((?:\S+)-(?:\S+)) -> ((?:\S+)-(?:\S+))')
        for p in data:
            m = regex.search(p)
            packages.append(m.group(1))
            if module._diff:
                diff['before'] += "%s-%s\n" % (m.group(1), m.group(2))
                diff['after'] += "%s-%s\n" % (m.group(1), m.group(3))
        if module.check_mode:
            module.exit_json(changed=True, msg="%s package(s) would be upgraded" % (len(data)), packages=packages, diff=diff)
        rc, stdout, stderr = module.run_command(cmdupgrade, check_rc=False)
        if rc == 0:
            module.exit_json(changed=True, msg='System upgraded', packages=packages, diff=diff)
        else:
            module.fail_json(msg="Could not upgrade")
    else:
        module.exit_json(changed=False, msg='Nothing to upgrade', packages=packages)

def remove_packages(module, pacman_path, packages):
    data = []
    diff = {
        'before': '',
        'after': '',
    }

    if module.params["recurse"] or module.params["force"]:
        if module.params["recurse"]:
            args = "Rs"
        if module.params["force"]:
            args = "Rdd"
        if module.params["recurse"] and module.params["force"]:
            args = "Rdds"
    else:
        args = "R"

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        installed, updated, unknown = query_package(module, pacman_path, package)
        if not installed:
            continue

        cmd = "%s -%s %s --noconfirm --noprogressbar" % (pacman_path, args, package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))

        if module._diff:
            d = stdout.split('\n')[2].split(' ')[2:]
            for i, pkg in enumerate(d):
                d[i] = re.sub('-[0-9].*$', '', d[i].split('/')[-1])
                diff['before'] += "%s\n" % pkg
            data.append('\n'.join(d))

        remove_c += 1

    if remove_c > 0:
        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c, diff=diff)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, pacman_path, state, packages, package_files):
    install_c = 0
    package_err = []
    message = ""
    data = []
    diff = {
        'before': '',
        'after': '',
    }

    to_install_repos = []
    to_install_files = []
    for i, package in enumerate(packages):
        # if the package is installed and state == present or state == latest and is up-to-date then skip
        installed, updated, latestError = query_package(module, pacman_path, package)
        if latestError and state == 'latest':
            package_err.append(package)

        if installed and (state == 'present' or (state == 'latest' and updated)):
            continue

        if package_files[i]:
            to_install_files.append(package_files[i])
        else:
            to_install_repos.append(package)

    if to_install_repos:
        cmd = "%s -S %s --noconfirm --noprogressbar --needed" % (pacman_path, " ".join(to_install_repos))
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to install %s: %s" % (" ".join(to_install_repos), stderr))

        data = stdout.split('\n')[3].split(' ')[2:]
        data = [ i for i in data if i != '' ]
        for i, pkg in enumerate(data):
            data[i] = re.sub('-[0-9].*$', '', data[i].split('/')[-1])
            if module._diff:
                diff['after'] += "%s\n" % pkg

        install_c += len(to_install_repos)

    if to_install_files:
        cmd = "%s -U %s --noconfirm --noprogressbar --needed" % (pacman_path, " ".join(to_install_files))
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to install %s: %s" % (" ".join(to_install_files), stderr))

        data = stdout.split('\n')[3].split(' ')[2:]
        data = [ i for i in data if i != '' ]
        for i, pkg in enumerate(data):
            data[i] = re.sub('-[0-9].*$', '', data[i].split('/')[-1])
            if module._diff:
                diff['after'] += "%s\n" % pkg

        install_c += len(to_install_files)

    if state == 'latest' and len(package_err) > 0:
        message = "But could not ensure 'latest' state for %s package(s) as remote version could not be fetched." % (package_err)

    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s). %s" % (install_c, message), diff=diff)

    module.exit_json(changed=False, msg="package(s) already installed. %s" % (message), diff=diff)

def check_packages(module, pacman_path, packages, state):
    would_be_changed = []
    diff = {
        'before': '',
        'after': '',
        'before_header': '',
        'after_header': ''
    }

    for package in packages:
        installed, updated, unknown = query_package(module, pacman_path, package)
        if ((state in ["present", "latest"] and not installed) or
                (state == "absent" and installed) or
                (state == "latest" and not updated)):
            would_be_changed.append(package)
    if would_be_changed:
        if state == "absent":
            state = "removed"

        if module._diff and (state == 'removed'):
            diff['before_header'] = 'removed'
            diff['before'] = '\n'.join(would_be_changed) + '\n'
        elif module._diff and ((state == 'present') or (state == 'latest')):
            diff['after_header'] = 'installed'
            diff['after'] = '\n'.join(would_be_changed) + '\n'

        module.exit_json(changed=True, msg="%s package(s) would be %s" % (
            len(would_be_changed), state), diff=diff)
    else:
        module.exit_json(changed=False, msg="package(s) already %s" % state, diff=diff)


def expand_package_groups(module, pacman_path, pkgs):
    expanded = []

    for pkg in pkgs:
        if pkg: # avoid empty strings
            cmd = "%s -Sgq %s" % (pacman_path, pkg)
            rc, stdout, stderr = module.run_command(cmd, check_rc=False)

            if rc == 0:
                # A group was found matching the name, so expand it
                for name in stdout.split('\n'):
                    name = name.strip()
                    if name:
                        expanded.append(name)
            else:
                expanded.append(pkg)

    return expanded


def main():
    module = AnsibleModule(
        argument_spec    = dict(
            name         = dict(aliases=['pkg', 'package'], type='list'),
            state        = dict(default='present', choices=['present', 'installed', "latest", 'absent', 'removed']),
            recurse      = dict(default=False, type='bool'),
            force        = dict(default=False, type='bool'),
            upgrade      = dict(default=False, type='bool'),
            update_cache = dict(default=False, aliases=['update-cache'], type='bool')
        ),
        required_one_of = [['name', 'update_cache', 'upgrade']],
        supports_check_mode = True)

    pacman_path = module.get_bin_path('pacman', True)

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    elif p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p["update_cache"] and not module.check_mode:
        update_package_db(module, pacman_path)
        if not (p['name'] or p['upgrade']):
            module.exit_json(changed=True, msg='Updated the package master lists')

    if p['update_cache'] and module.check_mode and not (p['name'] or p['upgrade']):
        module.exit_json(changed=True, msg='Would have updated the package cache')

    if p['upgrade']:
        upgrade(module, pacman_path)

    if p['name']:
        pkgs = expand_package_groups(module, pacman_path, p['name'])

        pkg_files = []
        for i, pkg in enumerate(pkgs):
            if not pkg: # avoid empty strings
                continue
            elif re.match(".*\.pkg\.tar(\.(gz|bz2|xz|lrz|lzo|Z))?$", pkg):
                # The package given is a filename, extract the raw pkg name from
                # it and store the filename
                pkg_files.append(pkg)
                pkgs[i] = re.sub('-[0-9].*$', '', pkgs[i].split('/')[-1])
            else:
                pkg_files.append(None)

        if module.check_mode:
            check_packages(module, pacman_path, pkgs, p['state'])

        if p['state'] in ['present', 'latest']:
            install_packages(module, pacman_path, p['state'], pkgs, pkg_files)
        elif p['state'] == 'absent':
            remove_packages(module, pacman_path, pkgs)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
