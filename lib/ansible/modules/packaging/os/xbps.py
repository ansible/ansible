#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2016 Dino Occhialini <dino.occhialini@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: xbps
short_description: Manage packages with XBPS
description:
    - Manage packages with the XBPS package manager.
author:
    - "Dino Occhialini (@dinoocch)"
    - "Michael Aldridge (@the-maldridge)"
version_added: "2.3"
options:
    name:
        description:
            - Name of the package to install, upgrade, or remove.
    state:
        description:
            - Desired state of the package.
        default: "present"
        choices: ["present", "absent", "latest"]
    recurse:
        description:
            - When removing a package, also remove its dependencies, provided
              that they are not required by other packages and were not
              explicitly installed by a user.
        type: bool
        default: 'no'
    update_cache:
        description:
            - Whether or not to refresh the master package lists. This can be
              run as part of a package installation or as a separate step.
        type: bool
        default: 'yes'
    upgrade:
        description:
            - Whether or not to upgrade whole system
        type: bool
        default: 'no'
'''

EXAMPLES = '''
# Install package foo
- xbps: name=foo state=present
# Upgrade package foo
- xbps: name=foo state=latest update_cache=yes
# Remove packages foo and bar
- xbps: name=foo,bar state=absent
# Recursively remove package foo
- xbps: name=foo state=absent recurse=yes
# Update package cache
- xbps: update_cache=yes
# Upgrade packages
- xbps: upgrade=yes
'''

RETURN = '''
msg:
    description: Message about results
    returned: success
    type: string
    sample: "System Upgraded"
packages:
    description: Packages that are affected/would be affected
    type: list
    sample: ["ansible"]
    returned: success
'''


import os

from ansible.module_utils.basic import AnsibleModule


def is_installed(xbps_output):
    """Returns package install state"""
    return bool(len(xbps_output))


def query_package(module, xbps_path, name, state="present"):
    """Returns Package info"""
    if state == "present":
        lcmd = "%s %s" % (xbps_path['query'], name)
        lrc, lstdout, lstderr = module.run_command(lcmd, check_rc=False)
        if not is_installed(lstdout):
            # package is not installed locally
            return False, False

        rcmd = "%s -Sun" % (xbps_path['install'])
        rrc, rstdout, rstderr = module.run_command(rcmd, check_rc=False)
        if rrc == 0 or rrc == 17:
            """Return True to indicate that the package is installed locally,
            and the result of the version number comparison to determine if the
            package is up-to-date"""
            return True, name not in rstdout

        return False, False


def update_package_db(module, xbps_path):
    """Returns True if update_package_db changed"""
    cmd = "%s -S" % (xbps_path['install'])
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        module.fail_json(msg="Could not update package db")
    if "avg rate" in stdout:
        return True
    else:
        return False


def upgrade(module, xbps_path):
    """Returns true is full upgrade succeeds"""
    cmdupgrade = "%s -uy" % (xbps_path['install'])
    cmdneedupgrade = "%s -un" % (xbps_path['install'])

    rc, stdout, stderr = module.run_command(cmdneedupgrade, check_rc=False)
    if rc == 0:
        if(len(stdout.splitlines()) == 0):
            module.exit_json(changed=False, msg='Nothing to upgrade')
        else:
            rc, stdout, stderr = module.run_command(cmdupgrade, check_rc=False)
            if rc == 0:
                module.exit_json(changed=True, msg='System upgraded')
            else:
                module.fail_json(msg="Could not upgrade")
    else:
        module.fail_json(msg="Could not upgrade")


def remove_packages(module, xbps_path, packages):
    """Returns true if package removal succeeds"""
    changed_packages = []
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        installed, updated = query_package(module, xbps_path, package)
        if not installed:
            continue

        cmd = "%s -y %s" % (xbps_path['remove'], package)
        rc, stdout, stderr = module.run_command(cmd, check_rc=False)

        if rc != 0:
            module.fail_json(msg="failed to remove %s" % (package))

        changed_packages.append(package)

    if len(changed_packages) > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" %
                         len(changed_packages), packages=changed_packages)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, xbps_path, state, packages):
    """Returns true if package install succeeds."""
    toInstall = []
    for i, package in enumerate(packages):
        """If the package is installed and state == present or state == latest
        and is up-to-date then skip"""
        installed, updated = query_package(module, xbps_path, package)
        if installed and (state == 'present' or
                          (state == 'latest' and updated)):
            continue

        toInstall.append(package)

    if len(toInstall) == 0:
        module.exit_json(changed=False, msg="Nothing to Install")

    cmd = "%s -y %s" % (xbps_path['install'], " ".join(toInstall))
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0 and not (state == 'latest' and rc == 17):
        module.fail_json(msg="failed to install %s" % (package))

    module.exit_json(changed=True, msg="installed %s package(s)"
                     % (len(toInstall)),
                     packages=toInstall)

    module.exit_json(changed=False, msg="package(s) already installed",
                     packages=[])


def check_packages(module, xbps_path, packages, state):
    """Returns change status of command"""
    would_be_changed = []
    for package in packages:
        installed, updated = query_package(module, xbps_path, package)
        if ((state in ["present", "latest"] and not installed) or
                (state == "absent" and installed) or
                (state == "latest" and not updated)):
            would_be_changed.append(package)
    if would_be_changed:
        if state == "absent":
            state = "removed"
        module.exit_json(changed=True, msg="%s package(s) would be %s" % (
            len(would_be_changed), state),
            packages=would_be_changed)
    else:
        module.exit_json(changed=False, msg="package(s) already %s" % state,
                         packages=[])


def main():
    """Returns, calling appropriate command"""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, aliases=['pkg', 'package'], type='list'),
            state=dict(default='present', choices=['present', 'installed',
                                                   'latest', 'absent',
                                                   'removed']),
            recurse=dict(default=False, type='bool'),
            force=dict(default=False, type='bool'),
            upgrade=dict(default=False, type='bool'),
            update_cache=dict(default=True, aliases=['update-cache'],
                              type='bool')
        ),
        required_one_of=[['name', 'update_cache', 'upgrade']],
        supports_check_mode=True)

    xbps_path = dict()
    xbps_path['install'] = module.get_bin_path('xbps-install', True)
    xbps_path['query'] = module.get_bin_path('xbps-query', True)
    xbps_path['remove'] = module.get_bin_path('xbps-remove', True)

    if not os.path.exists(xbps_path['install']):
        module.fail_json(msg="cannot find xbps, in path %s"
                         % (xbps_path['install']))

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    elif p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p["update_cache"] and not module.check_mode:
        changed = update_package_db(module, xbps_path)
        if p['name'] is None and not p['upgrade']:
            if changed:
                module.exit_json(changed=True,
                                 msg='Updated the package master lists')
            else:
                module.exit_json(changed=False,
                                 msg='Package list already up to date')

    if (p['update_cache'] and module.check_mode and not
            (p['name'] or p['upgrade'])):
        module.exit_json(changed=True,
                         msg='Would have updated the package cache')

    if p['upgrade']:
        upgrade(module, xbps_path)

    if p['name']:
        pkgs = p['name']

        if module.check_mode:
            check_packages(module, xbps_path, pkgs, p['state'])

        if p['state'] in ['present', 'latest']:
            install_packages(module, xbps_path, p['state'], pkgs)
        elif p['state'] == 'absent':
            remove_packages(module, xbps_path, pkgs)


if __name__ == "__main__":
    main()
