#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrik Lundin <patrik.lundin.swe@gmail.com>
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
import shlex

DOCUMENTATION = '''
---
module: openbsd_pkg
author: Patrik Lundin
version_added: "1.1"
short_description: Manage packages on OpenBSD.
description:
    - Manage packages on OpenBSD using the pkg tools.
options:
    name:
        required: true
        description:
        - Name of the package.
    state:
        required: true
        choices: [ present, latest, absent ]
        description:
          - C(present) will make sure the package is installed.
            C(latest) will make sure the latest version of the package is installed.
            C(absent) will make sure the specified package is not installed.
'''

EXAMPLES = '''
# Make sure nmap is installed
- openbsd_pkg: name=nmap state=present

# Make sure nmap is the latest version
- openbsd_pkg: name=nmap state=latest

# Make sure nmap is not installed
- openbsd_pkg: name=nmap state=absent
'''

# Function used for executing commands.
def execute_command(cmd, module):
    # Break command line into arguments.
    # This makes run_command() use shell=False which we need to not cause shell
    # expansion of special characters like '*'.
    cmd_args = shlex.split(cmd)
    return module.run_command(cmd_args)

# Function used for getting the name of a currently installed package.
def get_current_name(name, specific_version, module):
    info_cmd = 'pkg_info'
    (rc, stdout, stderr) = execute_command("%s" % (info_cmd), module)
    if rc != 0:
        return (rc, stdout, stderr)

    if specific_version:
        syntax = "%s"
    else:
        syntax = "%s-"

    for line in stdout.splitlines():
        if syntax % name in line:
            current_name = line.split()[0]

    return current_name

# Function used to find out if a package is currently installed.
def get_package_state(name, specific_version, module):
    info_cmd = 'pkg_info -e'

    if specific_version:
        syntax = "%s %s"
    else:
        syntax = "%s %s-*"

    rc, stdout, stderr = execute_command(syntax % (info_cmd, name), module)

    if rc == 0:
        return True
    else:
        return False

# Function used to make sure a package is present.
def package_present(name, installed_state, specific_version, module):
    if module.check_mode:
        install_cmd = 'pkg_add -Imn'
    else:
        install_cmd = 'pkg_add -Im'

    if installed_state is False:

        # Attempt to install the package
        (rc, stdout, stderr) = execute_command("%s %s" % (install_cmd, name), module)

        # The behaviour of pkg_add is a bit different depending on if a
        # specific version is supplied or not.
        #
        # When a specific version is supplied the return code will be 0 when
        # a package is found and 1 when it is not, if a version is not
        # supplied the tool will exit 0 in both cases:
        if specific_version:
            # Depend on the return code.
            if rc:
                changed=False
        else:
            # Depend on stderr instead.
            if stderr:
                # There is a corner case where having an empty directory in
                # installpath prior to the right location will result in a
                # "file:/local/package/directory/ is empty" message on stderr
                # while still installing the package, so we need to look for
                # for a message like "packagename-1.0: ok" just in case.
                match = re.search("\W%s-[^:]+: ok\W" % name, stdout)
                if match:
                    # It turns out we were able to install the package.
                    pass
                else:
                    # We really did fail, fake the return code.
                    rc = 1
                    changed=False

        if rc == 0:
            if module.check_mode:
                module.exit_json(changed=True)

            changed=True

    else:
        rc = 0
        stdout = ''
        stderr = ''
        changed=False

    return (rc, stdout, stderr, changed)

# Function used to make sure a package is the latest available version.
def package_latest(name, installed_state, specific_version, module):
    if module.check_mode:
        upgrade_cmd = 'pkg_add -umn'
    else:
        upgrade_cmd = 'pkg_add -um'

    pre_upgrade_name = ''

    if installed_state is True:

        # Fetch name of currently installed package
        pre_upgrade_name = get_current_name(name, specific_version, module)

        # Attempt to upgrade the package
        (rc, stdout, stderr) = execute_command("%s %s" % (upgrade_cmd, name), module)

        # Look for output looking something like "nmap-6.01->6.25: ok" to see if
        # something changed (or would have changed). Use \W to delimit the match
        # from progress meter output.
        match = re.search("\W%s->.+: ok\W" % pre_upgrade_name, stdout)
        if match:
            if module.check_mode:
                module.exit_json(changed=True)

            changed = True
        else:
            changed = False

        # FIXME: This part is problematic. Based on the issues mentioned (and
        # handled) in package_present() it is not safe to blindly trust stderr
        # as an indicator that the command failed, and in the case with
        # empty installpath directories this will break.
        #
        # For now keep this safeguard here, but ignore it if we managed to
        # parse out a successful update above. This way we will report a
        # successful run when we actually modify something but fail
        # otherwise.
        if changed != True:
            if stderr:
                rc=1

        return (rc, stdout, stderr, changed)

    else:
        # If package was not installed at all just make it present.
        return package_present(name, installed_state, specific_version, module)

# Function used to make sure a package is not installed.
def package_absent(name, installed_state, module):
    if module.check_mode:
        remove_cmd = 'pkg_delete -In'
    else:
        remove_cmd = 'pkg_delete -I'

    if installed_state is True:

        # Attempt to remove the package
        rc, stdout, stderr = execute_command("%s %s" % (remove_cmd, name), module)

        if rc == 0:
            if module.check_mode:
                module.exit_json(changed=True)

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
            name = dict(required=True),
            state = dict(required=True, choices=['absent', 'installed', 'latest', 'present', 'removed']),
        ),
        supports_check_mode = True
    )

    name      = module.params['name']
    state     = module.params['state']

    rc = 0
    stdout = ''
    stderr = ''
    result = {}
    result['name'] = name
    result['state'] = state

    # Decide if the name contains a version number.
    # This regex is based on packages-specs(7).
    match = re.search("-[0-9]", name)
    if match:
        specific_version = True
    else:
        specific_version = False

    # Get package state
    installed_state = get_package_state(name, specific_version, module)

    # Perform requested action
    if state in ['installed', 'present']:
        (rc, stdout, stderr, changed) = package_present(name, installed_state, specific_version, module)
    elif state in ['absent', 'removed']:
        (rc, stdout, stderr, changed) = package_absent(name, installed_state, module)
    elif state == 'latest':
        (rc, stdout, stderr, changed) = package_latest(name, installed_state, specific_version, module)

    if rc != 0:
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    result['changed'] = changed

    module.exit_json(**result)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
