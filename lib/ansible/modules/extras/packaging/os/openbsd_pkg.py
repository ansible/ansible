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
import syslog

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

# Specify a pkg flavour with '--'
- openbsd_pkg: name=vim--nox11 state=present

# Specify the default flavour to avoid ambiguity errors
- openbsd_pkg: name=vim-- state=present

# Update all packages on the system
- openbsd_pkg: name=* state=latest
'''

# Control if we write debug information to syslog.
debug = False

# Function used for executing commands.
def execute_command(cmd, module):
    if debug:
        syslog.syslog("execute_command(): cmd = %s" % cmd)
    # Break command line into arguments.
    # This makes run_command() use shell=False which we need to not cause shell
    # expansion of special characters like '*'.
    cmd_args = shlex.split(cmd)
    return module.run_command(cmd_args)

# Function used for getting the name of a currently installed package.
def get_current_name(name, pkg_spec, module):
    info_cmd = 'pkg_info'
    (rc, stdout, stderr) = execute_command("%s" % (info_cmd), module)
    if rc != 0:
        return (rc, stdout, stderr)

    if pkg_spec['version']:
        pattern = "^%s" % name
    elif pkg_spec['flavor']:
        pattern = "^%s-.*-%s\s" % (pkg_spec['stem'], pkg_spec['flavor'])
    else:
        pattern = "^%s-" % pkg_spec['stem']

    if debug:
        syslog.syslog("get_current_name(): pattern = %s" % pattern)

    for line in stdout.splitlines():
        if debug:
            syslog.syslog("get_current_name: line = %s" % line)
        match = re.search(pattern, line)
        if match:
            current_name = line.split()[0]

    return current_name

# Function used to find out if a package is currently installed.
def get_package_state(name, pkg_spec, module):
    info_cmd = 'pkg_info -e'

    if pkg_spec['version']:
        command = "%s %s" % (info_cmd, name)
    elif pkg_spec['flavor']:
        command = "%s %s-*-%s" % (info_cmd, pkg_spec['stem'], pkg_spec['flavor'])
    else:
        command = "%s %s-*" % (info_cmd, pkg_spec['stem'])

    rc, stdout, stderr = execute_command(command, module)

    if (stderr):
        module.fail_json(msg="failed in get_package_state(): " + stderr)

    if rc == 0:
        return True
    else:
        return False

# Function used to make sure a package is present.
def package_present(name, installed_state, pkg_spec, module):
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
        if pkg_spec['version']:
            # Depend on the return code.
            if debug:
                syslog.syslog("package_present(): depending on return code")
            if rc:
                changed=False
        else:
            # Depend on stderr instead.
            if debug:
                syslog.syslog("package_present(): depending on stderr")
            if stderr:
                # There is a corner case where having an empty directory in
                # installpath prior to the right location will result in a
                # "file:/local/package/directory/ is empty" message on stderr
                # while still installing the package, so we need to look for
                # for a message like "packagename-1.0: ok" just in case.
                match = re.search("\W%s-[^:]+: ok\W" % name, stdout)
                if match:
                    # It turns out we were able to install the package.
                    if debug:
                        syslog.syslog("package_present(): we were able to install package")
                    pass
                else:
                    # We really did fail, fake the return code.
                    if debug:
                        syslog.syslog("package_present(): we really did fail")
                    rc = 1
                    changed=False
            else:
                if debug:
                    syslog.syslog("package_present(): stderr was not set")

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
def package_latest(name, installed_state, pkg_spec, module):
    if module.check_mode:
        upgrade_cmd = 'pkg_add -umn'
    else:
        upgrade_cmd = 'pkg_add -um'

    pre_upgrade_name = ''

    if installed_state is True:

        # Fetch name of currently installed package.
        pre_upgrade_name = get_current_name(name, pkg_spec, module)

        if debug:
            syslog.syslog("package_latest(): pre_upgrade_name = %s" % pre_upgrade_name)

        # Attempt to upgrade the package.
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
        if debug:
            syslog.syslog("package_latest(): package is not installed, calling package_present()")
        return package_present(name, installed_state, pkg_spec, module)

# Function used to make sure a package is not installed.
def package_absent(name, installed_state, module):
    if module.check_mode:
        remove_cmd = 'pkg_delete -In'
    else:
        remove_cmd = 'pkg_delete -I'

    if installed_state is True:

        # Attempt to remove the package.
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

# Function used to parse the package name based on packages-specs(7).
# The general name structure is "stem-version[-flavors]".
def parse_package_name(name, pkg_spec, module):
    # Do some initial matches so we can base the more advanced regex on that.
    version_match = re.search("-[0-9]", name)
    versionless_match = re.search("--", name)

    # Stop if someone is giving us a name that both has a version and is
    # version-less at the same time.
    if version_match and versionless_match:
        module.fail_json(msg="Package name both has a version and is version-less: " + name)

    # If name includes a version.
    if version_match:
        match = re.search("^(?P<stem>.*)-(?P<version>[0-9][^-]*)(?P<flavor_separator>-)?(?P<flavor>[a-z].*)?$", name)
        if match:
            pkg_spec['stem']              = match.group('stem')
            pkg_spec['version_separator'] = '-'
            pkg_spec['version']           = match.group('version')
            pkg_spec['flavor_separator']  = match.group('flavor_separator')
            pkg_spec['flavor']            = match.group('flavor')
        else:
            module.fail_json(msg="Unable to parse package name at version_match: " + name)

    # If name includes no version but is version-less ("--").
    elif versionless_match:
        match = re.search("^(?P<stem>.*)--(?P<flavor>[a-z].*)?$", name)
        if match:
            pkg_spec['stem']              = match.group('stem')
            pkg_spec['version_separator'] = '-'
            pkg_spec['version']           = None
            pkg_spec['flavor_separator']  = '-'
            pkg_spec['flavor']            = match.group('flavor')
        else:
            module.fail_json(msg="Unable to parse package name at versionless_match: " + name)

    # If name includes no version, and is not version-less, it is all a stem.
    else:
        match = re.search("^(?P<stem>.*)$", name)
        if match:
            pkg_spec['stem']              = match.group('stem')
            pkg_spec['version_separator'] = None
            pkg_spec['version']           = None
            pkg_spec['flavor_separator']  = None
            pkg_spec['flavor']            = None
        else:
            module.fail_json(msg="Unable to parse package name at else: " + name)

    # Sanity check that there are no trailing dashes in flavor.
    # Try to stop strange stuff early so we can be strict later.
    if pkg_spec['flavor']:
        match = re.search("-$", pkg_spec['flavor'])
        if match:
            module.fail_json(msg="Trailing dash in flavor: " + pkg_spec['flavor'])

# Function used for upgrading all installed packages.
def upgrade_packages(module):
    if module.check_mode:
        upgrade_cmd = 'pkg_add -Imnu'
    else:
        upgrade_cmd = 'pkg_add -Imu'

    # Attempt to upgrade all packages.
    rc, stdout, stderr = execute_command("%s" % upgrade_cmd, module)

    # Try to find any occurance of a package changing version like:
    # "bzip2-1.0.6->1.0.6p0: ok".
    match = re.search("\W\w.+->.+: ok\W", stdout)
    if match:
        if module.check_mode:
            module.exit_json(changed=True)

        changed=True

    else:
        changed=False

    # It seems we can not trust the return value, so depend on the presence of
    # stderr to know if something failed.
    if stderr:
        rc = 1
    else:
        rc = 0

    return (rc, stdout, stderr, changed)

# ===========================================
# Main control flow.

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

    if name == '*':
        if state != 'latest':
            module.fail_json(msg="the package name '*' is only valid when using state=latest")
        else:
            # Perform an upgrade of all installed packages.
            (rc, stdout, stderr, changed) = upgrade_packages(module)
    else:
        # Parse package name and put results in the pkg_spec dictionary.
        pkg_spec = {}
        parse_package_name(name, pkg_spec, module)

        # Get package state.
        installed_state = get_package_state(name, pkg_spec, module)

        # Perform requested action.
        if state in ['installed', 'present']:
            (rc, stdout, stderr, changed) = package_present(name, installed_state, pkg_spec, module)
        elif state in ['absent', 'removed']:
            (rc, stdout, stderr, changed) = package_absent(name, installed_state, module)
        elif state == 'latest':
            (rc, stdout, stderr, changed) = package_latest(name, installed_state, pkg_spec, module)

    if rc != 0:
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    result['changed'] = changed

    module.exit_json(**result)

# Import module snippets.
from ansible.module_utils.basic import *
main()
