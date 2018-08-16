#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Kevin Brebanov <https://github.com/kbrebanov>
# Based on pacman (Afterburn <https://github.com/afterburn>, Aaron Bull Schaefer <aaron@elasticdog.com>)
# and apt (Matthew Williams <matthew@flowroute.com>) modules.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: apk
short_description: Manages apk packages
description:
  - Manages I(apk) packages for Alpine Linux.
author: "Kevin Brebanov (@kbrebanov)"
version_added: "2.0"
options:
  available:
    description:
      - During upgrade, reset versioned world dependencies and change logic to prefer replacing or downgrading packages (instead of holding them)
        if the currently installed package is no longer available from any repository.
    type: bool
    default: 'no'
    version_added: "2.4"
  name:
    description:
      - A package name, like C(foo), or multiple packages, like C(foo, bar).
  repository:
    description:
      - A package repository or multiple repositories.
        Unlike with the underlying apk command, this list will override the system repositories rather than supplement them.
    version_added: "2.4"
  state:
    description:
      - Indicates the desired package(s) state.
      - C(present) ensures the package(s) is/are present.
      - C(absent) ensures the package(s) is/are absent.
      - C(latest) ensures the package(s) is/are present and the latest version(s).
    default: present
    choices: [ "present", "absent", "latest" ]
  update_cache:
    description:
      - Update repository indexes. Can be run with other steps or on it's own.
    type: bool
    default: 'no'
  upgrade:
    description:
      - Upgrade all installed packages to their latest version.
    type: bool
    default: 'no'
notes:
  - '"name" and "upgrade" are mutually exclusive.'
  - When used with a `loop:` each package will be processed individually, it is much more efficient to pass the list directly to the `name` option.
'''

EXAMPLES = '''
# Update repositories and install "foo" package
- apk:
    name: foo
    update_cache: yes

# Update repositories and install "foo" and "bar" packages
- apk:
    name: foo,bar
    update_cache: yes

# Remove "foo" package
- apk:
    name: foo
    state: absent

# Remove "foo" and "bar" packages
- apk:
    name: foo,bar
    state: absent

# Install the package "foo"
- apk:
    name: foo
    state: present

# Install the packages "foo" and "bar"
- apk:
    name: foo,bar
    state: present

# Update repositories and update package "foo" to latest version
- apk:
    name: foo
    state: latest
    update_cache: yes

# Update repositories and update packages "foo" and "bar" to latest versions
- apk:
    name: foo,bar
    state: latest
    update_cache: yes

# Update all installed packages to the latest versions
- apk:
    upgrade: yes

# Upgrade / replace / downgrade / uninstall all installed packages to the latest versions available
- apk:
    available: yes
    upgrade: yes

# Update repositories as a separate step
- apk:
    update_cache: yes

# Install package from a specific repository
- apk:
    name: foo
    state: latest
    update_cache: yes
    repository: http://dl-3.alpinelinux.org/alpine/edge/main
'''

RETURN = '''
packages:
    description: a list of packages that have been changed
    returned: when packages have changed
    type: list
    sample: ['package', 'other-package']
'''

import re
# Import module snippets.
from ansible.module_utils.basic import AnsibleModule


def parse_for_packages(stdout):
    packages = []
    data = stdout.split('\n')
    regex = re.compile(r'^\(\d+/\d+\)\s+\S+\s+(\S+)')
    for l in data:
        p = regex.search(l)
        if p:
            packages.append(p.group(1))
    return packages


def update_package_db(module, exit):
    cmd = "%s update" % (APK_PATH)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc != 0:
        module.fail_json(msg="could not update package db", stdout=stdout, stderr=stderr)
    elif exit:
        module.exit_json(changed=True, msg='updated repository indexes', stdout=stdout, stderr=stderr)
    else:
        return True


def query_toplevel(module, name):
    # /etc/apk/world contains a list of top-level packages separated by ' ' or \n
    # packages may contain repository (@) or version (=<>~) separator characters or start with negation !
    regex = re.compile(r'^' + re.escape(name) + r'([@=<>~].+)?$')
    with open('/etc/apk/world') as f:
        content = f.read().split()
        for p in content:
            if regex.search(p):
                return True
    return False


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
    search_pattern = r"(%s)-[\d\.\w]+-[\d\w]+\s+(.)\s+[\d\.\w]+-[\d\w]+\s+" % (re.escape(name))
    match = re.search(search_pattern, stdout)
    if match and match.group(2) == "<":
        return False
    return True


def query_virtual(module, name):
    cmd = "%s -v info --description %s" % (APK_PATH, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    search_pattern = r"^%s: virtual meta package" % (re.escape(name))
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


def upgrade_packages(module, available):
    if module.check_mode:
        cmd = "%s upgrade --simulate" % (APK_PATH)
    else:
        cmd = "%s upgrade" % (APK_PATH)
    if available:
        cmd = "%s --available" % cmd
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    packagelist = parse_for_packages(stdout)
    if rc != 0:
        module.fail_json(msg="failed to upgrade packages", stdout=stdout, stderr=stderr, packages=packagelist)
    if re.search(r'^OK', stdout):
        module.exit_json(changed=False, msg="packages already upgraded", stdout=stdout, stderr=stderr, packages=packagelist)
    module.exit_json(changed=True, msg="upgraded packages", stdout=stdout, stderr=stderr, packages=packagelist)


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
            if not query_toplevel(module, name):
                to_install.append(name)
            elif state == 'latest' and not query_latest(module, name):
                to_upgrade.append(name)
    if to_upgrade:
        upgrade = True
    if not to_install and not upgrade:
        module.exit_json(changed=False, msg="package(s) already installed")
    packages = " ".join(to_install + to_upgrade)
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
    packagelist = parse_for_packages(stdout)
    if rc != 0:
        module.fail_json(msg="failed to install %s" % (packages), stdout=stdout, stderr=stderr, packages=packagelist)
    module.exit_json(changed=True, msg="installed %s package(s)" % (packages), stdout=stdout, stderr=stderr, packages=packagelist)


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
    packagelist = parse_for_packages(stdout)
    # Check to see if packages are still present because of dependencies
    for name in installed:
        if query_package(module, name):
            rc = 1
            break
    if rc != 0:
        module.fail_json(msg="failed to remove %s package(s)" % (names), stdout=stdout, stderr=stderr, packages=packagelist)
    module.exit_json(changed=True, msg="removed %s package(s)" % (names), stdout=stdout, stderr=stderr, packages=packagelist)

# ==========================================
# Main control flow.


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'installed', 'absent', 'removed', 'latest']),
            name=dict(type='list'),
            repository=dict(type='list'),
            update_cache=dict(default='no', type='bool'),
            upgrade=dict(default='no', type='bool'),
            available=dict(default='no', type='bool'),
        ),
        required_one_of=[['name', 'update_cache', 'upgrade']],
        mutually_exclusive=[['name', 'upgrade']],
        supports_check_mode=True
    )

    # Set LANG env since we parse stdout
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    global APK_PATH
    APK_PATH = module.get_bin_path('apk', required=True)

    p = module.params

    # add repositories to the APK_PATH
    if p['repository']:
        for r in p['repository']:
            APK_PATH = "%s --repository %s --repositories-file /dev/null" % (APK_PATH, r)

    # normalize the state parameter
    if p['state'] in ['present', 'installed']:
        p['state'] = 'present'
    if p['state'] in ['absent', 'removed']:
        p['state'] = 'absent'

    if p['update_cache']:
        update_package_db(module, not p['name'] and not p['upgrade'])

    if p['upgrade']:
        upgrade_packages(module, p['available'])

    if p['state'] in ['present', 'latest']:
        install_packages(module, p['name'], p['state'])
    elif p['state'] == 'absent':
        remove_packages(module, p['name'])


if __name__ == '__main__':
    main()
