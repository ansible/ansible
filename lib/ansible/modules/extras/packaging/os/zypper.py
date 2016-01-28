#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2013, Patrick Callahan <pmc@patrickcallahan.com>
# based on
#     openbsd_pkg
#         (c) 2013
#         Patrik Lundin <patrik.lundin.swe@gmail.com>
#
#     yum
#         (c) 2012, Red Hat, Inc
#         Written by Seth Vidal <skvidal at fedoraproject.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import re

DOCUMENTATION = '''
---
module: zypper
author:
    - "Patrick Callahan (@dirtyharrycallahan)"
    - "Alexander Gubin (@alxgu)"
version_added: "1.2"
short_description: Manage packages on SUSE and openSUSE
description:
    - Manage packages on SUSE and openSUSE using the zypper and rpm tools.
options:
    name:
        description:
        - package name or package specifier with version C(name) or C(name-1.0). You can also pass a url or a local path to a rpm file.
        required: true
        aliases: [ 'pkg' ]
    state:
        description:
          - C(present) will make sure the package is installed.
            C(latest)  will make sure the latest version of the package is installed.
            C(absent)  will make sure the specified package is not installed.
        required: false
        choices: [ present, latest, absent ]
        default: "present"
    type:
        description:
          - The type of package to be operated on.
        required: false
        choices: [ package, patch, pattern, product, srcpackage ]
        default: "package"
        version_added: "2.0"
    disable_gpg_check:
        description:
          - Whether to disable to GPG signature checking of the package
            signature being installed. Has an effect only if state is
            I(present) or I(latest).
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: []
    disable_recommends:
        version_added: "1.8"
        description:
          - Corresponds to the C(--no-recommends) option for I(zypper). Default behavior (C(yes)) modifies zypper's default behavior; C(no) does install recommended packages. 
        required: false
        default: "yes"
        choices: [ "yes", "no" ]

notes: []
# informational: requirements for nodes
requirements: [ zypper, rpm ]
'''

EXAMPLES = '''
# Install "nmap"
- zypper: name=nmap state=present

# Install apache2 with recommended packages
- zypper: name=apache2 state=present disable_recommends=no

# Remove the "nmap" package
- zypper: name=nmap state=absent

# Install the nginx rpm from a remote repo
- zypper: name=http://nginx.org/packages/sles/12/x86_64/RPMS/nginx-1.8.0-1.sles12.ngx.x86_64.rpm state=present

# Install local rpm file
- zypper: name=/tmp/fancy-software.rpm state=present
'''

# Function used for getting zypper version
def zypper_version(module):
    """Return (rc, message) tuple"""
    cmd = ['/usr/bin/zypper', '-V']
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)
    if rc == 0:
        return rc, stdout
    else:
        return rc, stderr

# Function used for getting versions of currently installed packages.
def get_current_version(m, packages):
    cmd = ['/bin/rpm', '-q', '--qf', '%{NAME} %{VERSION}-%{RELEASE}\n']
    cmd.extend(packages)

    rc, stdout, stderr = m.run_command(cmd, check_rc=False)

    current_version = {}
    rpmoutput_re = re.compile('^(\S+) (\S+)$')

    for stdoutline in stdout.splitlines():
        match = rpmoutput_re.match(stdoutline)
        if match == None:
            return None
        package = match.group(1)
        version = match.group(2)
        current_version[package] = version

    for package in packages:
        if package not in current_version:
            print package + ' was not returned by rpm \n'
            return None

    return current_version


# Function used to find out if a package is currently installed.
def get_package_state(m, packages):
    for i in range(0, len(packages)):
        # Check state of a local rpm-file
        if ".rpm" in packages[i]:
            # Check if rpm file is available
            package = packages[i]
            if not os.path.isfile(package) and not '://' in package:
                stderr = "No Package file matching '%s' found on system" % package
                m.fail_json(msg=stderr, rc=1)
            # Get packagename from rpm file
            cmd = ['/bin/rpm', '--query', '--qf', '%{NAME}', '--package']
            cmd.append(package)
            rc, stdout, stderr = m.run_command(cmd, check_rc=False)
            packages[i] = stdout

    cmd = ['/bin/rpm', '--query', '--qf', 'package %{NAME} is installed\n']
    cmd.extend(packages)

    rc, stdout, stderr = m.run_command(cmd, check_rc=False)

    installed_state = {}
    rpmoutput_re = re.compile('^package (\S+) (.*)$')
    for stdoutline in stdout.splitlines():
        match = rpmoutput_re.match(stdoutline)
        if match == None:
            continue
        package = match.group(1)
        result = match.group(2)
        if result == 'is installed':
            installed_state[package] = True
        else:
            installed_state[package] = False

    return installed_state

# Function used to make sure a package is present.
def package_present(m, name, installed_state, package_type, disable_gpg_check, disable_recommends, old_zypper):
    packages = []
    for package in name:
        if package not in installed_state or installed_state[package] is False:
            packages.append(package)
    if len(packages) != 0:
        cmd = ['/usr/bin/zypper', '--non-interactive']
        # add global options before zypper command
        if disable_gpg_check:
            cmd.append('--no-gpg-checks')
        cmd.extend(['install', '--auto-agree-with-licenses', '-t', package_type])
        # add install parameter
        if disable_recommends and not old_zypper:
            cmd.append('--no-recommends')
        cmd.extend(packages)
        rc, stdout, stderr = m.run_command(cmd, check_rc=False)

        if rc == 0:
            changed=True
        else:
            changed=False
    else:
        rc = 0
        stdout = ''
        stderr = ''
        changed=False

    return (rc, stdout, stderr, changed)

# Function used to make sure a package is the latest available version.
def package_latest(m, name, installed_state, package_type, disable_gpg_check, disable_recommends, old_zypper):

    # first of all, make sure all the packages are installed
    (rc, stdout, stderr, changed) = package_present(m, name, installed_state, package_type, disable_gpg_check, disable_recommends, old_zypper)

    # return if an error occured while installation
    # otherwise error messages will be lost and user doesn`t see any error
    if rc:
        return (rc, stdout, stderr, changed)

    # if we've already made a change, we don't have to check whether a version changed
    if not changed:
        pre_upgrade_versions = get_current_version(m, name)

    cmd = ['/usr/bin/zypper', '--non-interactive']

    if disable_gpg_check:
        cmd.append('--no-gpg-checks')

    if old_zypper:
        cmd.extend(['install', '--auto-agree-with-licenses', '-t', package_type])
    else:
        cmd.extend(['update', '--auto-agree-with-licenses', '-t', package_type])

    cmd.extend(name)
    rc, stdout, stderr = m.run_command(cmd, check_rc=False)

    # if we've already made a change, we don't have to check whether a version changed
    if not changed:
        post_upgrade_versions = get_current_version(m, name)
        if pre_upgrade_versions != post_upgrade_versions:
            changed = True

    return (rc, stdout, stderr, changed)

# Function used to make sure a package is not installed.
def package_absent(m, name, installed_state, package_type, old_zypper):
    packages = []
    for package in name:
        if package not in installed_state or installed_state[package] is True:
            packages.append(package)
    if len(packages) != 0:
        cmd = ['/usr/bin/zypper', '--non-interactive', 'remove', '-t', package_type]
        cmd.extend(packages)
        rc, stdout, stderr = m.run_command(cmd)

        if rc == 0:
            changed=True
        else:
            changed=False
    else:
        rc = 0
        stdout = ''
        stderr = ''
        changed=False

    return (rc, stdout, stderr, changed)

# ===========================================
# Main control flow

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, aliases=['pkg'], type='list'),
            state = dict(required=False, default='present', choices=['absent', 'installed', 'latest', 'present', 'removed']),
            type = dict(required=False, default='package', choices=['package', 'patch', 'pattern', 'product', 'srcpackage']),
            disable_gpg_check = dict(required=False, default='no', type='bool'),
            disable_recommends = dict(required=False, default='yes', type='bool'),
        ),
        supports_check_mode = False
    )


    params = module.params

    name  = params['name']
    state = params['state']
    type_ = params['type']
    disable_gpg_check = params['disable_gpg_check']
    disable_recommends = params['disable_recommends']

    rc = 0
    stdout = ''
    stderr = ''
    result = {}
    result['name'] = name
    result['state'] = state

    rc, out = zypper_version(module)
    match = re.match(r'zypper\s+(\d+)\.(\d+)\.(\d+)', out)
    if not match or  int(match.group(1)) > 0:
        old_zypper = False
    else:
        old_zypper = True

    # Get package state
    installed_state = get_package_state(module, name)

    # Perform requested action
    if state in ['installed', 'present']:
        (rc, stdout, stderr, changed) = package_present(module, name, installed_state, type_, disable_gpg_check, disable_recommends, old_zypper)
    elif state in ['absent', 'removed']:
        (rc, stdout, stderr, changed) = package_absent(module, name, installed_state, type_, old_zypper)
    elif state == 'latest':
        (rc, stdout, stderr, changed) = package_latest(module, name, installed_state, type_, disable_gpg_check, disable_recommends, old_zypper)

    if rc != 0:
        if stderr:
            module.fail_json(msg=stderr, rc=rc)
        else:
            module.fail_json(msg=stdout, rc=rc)

    result['changed'] = changed
    result['rc'] = rc

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
