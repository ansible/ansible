#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Kevin Brebanov <https://github.com/kbrebanov>
# Based on pacman (Afterburn <http://github.com/afterburn>, Aaron Bull Schaefer <aaron@elasticdog.com>)
# and apt (Matthew Williams <matthew@flowroute.com>>) modules.
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
module: apk
short_description: Manages apk packages
description:
  - Manages I(apk) packages for Alpine Linux.
version_added: "2.0"
options:
  name:
    description:
      - A package name, like C(foo), or mutliple packages, like C(foo, bar).
    required: false
    default: null
  state:
    description:
      - Indicates the desired package(s) state.
      - C(present) ensures the package(s) is/are present.
      - C(absent) ensures the package(s) is/are absent.
      - C(latest) ensures the package(s) is/are present and the latest version(s).
    required: false
    default: present
    choices: [ "present", "absent", "latest" ]
  update_cache:
    description:
      - Update repository indexes. Can be run with other steps or on it's own.
    required: false
    default: no
    choices: [ "yes", "no" ]
  upgrade:
    description:
      - Upgrade all installed packages to their latest version.
    required: false
    default: no
    choices: [ "yes", "no" ]
notes:
  - '"name" and "upgrade" are mutually exclusive.'
'''

EXAMPLES = '''
# Update repositories and install "foo" package
- apk: name=foo update_cache=yes

# Update repositories and install "foo" and "bar" packages
- apk: name=foo,bar update_cache=yes

# Remove "foo" package
- apk: name=foo state=absent

# Remove "foo" and "bar" packages
- apk: name=foo,bar state=absent

# Install the package "foo"
- apk: name=foo state=present

# Install the packages "foo" and "bar"
- apk: name=foo,bar state=present

# Update repositories and update package "foo" to latest version
- apk: name=foo state=latest update_cache=yes

# Update repositories and update packages "foo" and "bar" to latest versions
- apk: name=foo,bar state=latest update_cache=yes

# Update all installed packages to the latest versions
- apk: upgrade=yes

# Update repositories as a separate step
- apk: update_cache=yes
'''

import os
import re

def update_package_db(module):
    cmd = "%s update" % (APK_PATH)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return True
    else:
        module.fail_json(msg="could not update package db")

def query_package(module, name):
    cmd = "%s -v info --installed %s" % (APK_PATH, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return True
    else:
        return False

def query_latest(module, name):
    cmd = "%s version %s" % (APK_PATH, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    search_pattern = "(%s)-[\d\.\w]+-[\d\w]+\s+(.)\s+[\d\.\w]+-[\d\w]+\s+" % (name)
    match = re.search(search_pattern, stdout)
    if match and match.group(2) == "<":
        return False
    return True

def query_virtual(module, name):
    cmd = "%s -v info --description %s" % (APK_PATH, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    search_pattern = "^%s: virtual meta package" % (name)
    if re.search(search_pattern, stdout):
        return True
    return False

def get_dependencies(module, name):
    cmd = "%s -v info --depends %s" % (APK_PATH, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    dependencies = stdout.split()
    if len(dependencies) > 1:
        return dependencies[1:]
    else:
        return []

def upgrade_packages(module):
    if module.check_mode:
        cmd = "%s upgrade --simulate" % (APK_PATH)
    else:
        cmd = "%s upgrade" % (APK_PATH)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="failed to upgrade packages")
    if re.search('^OK', stdout):
        module.exit_json(changed=False, msg="packages already upgraded")
    module.exit_json(changed=True, msg="upgraded packages")

def install_packages(module, names, state):
    upgrade = False
    to_install = []
    to_upgrade = []
    for name in names:
        # Check if virtual package
        if query_virtual(module, name):
            # Get virtual package dependencies
            dependencies = get_dependencies(module, name)
            for dependency in dependencies:
                if state == 'latest' and not query_latest(module, dependency):
                    to_upgrade.append(dependency)
        else:
            if not query_package(module, name):
                to_install.append(name)
            elif state == 'latest' and not query_latest(module, name):
                to_upgrade.append(name)
    if to_upgrade:
        upgrade = True
    if not to_install and not upgrade:
        module.exit_json(changed=False, msg="package(s) already installed")
    packages = " ".join(to_install) + " ".join(to_upgrade)
    if upgrade:
        if module.check_mode:
            cmd = "%s add --upgrade --simulate %s" % (APK_PATH, packages)
        else:
            cmd = "%s add --upgrade %s" % (APK_PATH, packages)
    else:
        if module.check_mode:
            cmd = "%s add --simulate %s" % (APK_PATH, packages)
        else:
            cmd = "%s add %s" % (APK_PATH, packages)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="failed to install %s" % (packages))
    module.exit_json(changed=True, msg="installed %s package(s)" % (packages))

def remove_packages(module, names):
    installed = []
    for name in names:
        if query_package(module, name):
            installed.append(name)
    if not installed:
        module.exit_json(changed=False, msg="package(s) already removed")
    names = " ".join(installed)
    if module.check_mode:
        cmd = "%s del --purge --simulate %s" % (APK_PATH, names)
    else:
        cmd = "%s del --purge %s" % (APK_PATH, names)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="failed to remove %s package(s)" % (names))
    module.exit_json(changed=True, msg="removed %s package(s)" % (names))

# ==========================================
# Main control flow.

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'installed', 'absent', 'removed', 'latest']),
            name = dict(type='list'),
            update_cache = dict(default='no', type='bool'),
            upgrade = dict(default='no', type='bool'),
        ),
        required_one_of = [['name', 'update_cache', 'upgrade']],
        mutually_exclusive = [['name', 'upgrade']],
        supports_check_mode = True
    )

    # Set LANG env since we parse stdout
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    global APK_PATH
    APK_PATH = module.get_bin_path('apk', required=True)

    p = module.params

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    if p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p['update_cache']:
        update_package_db(module)
        if not p['name']:
            module.exit_json(changed=True, msg='updated repository indexes')

    if p['upgrade']:
        upgrade_packages(module)

    if p['state'] in ['present', 'latest']:
        install_packages(module, p['name'], p['state'])
    elif p['state'] == 'absent':
        remove_packages(module, p['name'])

# Import module snippets.
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
