#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrik Lundin <patrik@sigterm.se>
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

import os
import re
import shlex
import sqlite3

DOCUMENTATION = '''
---
module: openbsd_pkg
author: "Patrik Lundin (@eest)"
version_added: "1.1"
short_description: Manage packages on OpenBSD.
description:
    - Manage packages on OpenBSD using the pkg tools.
requirements: [ "python >= 2.5" ]
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
    build:
        required: false
        choices: [ yes, no ]
        default: no
        description:
          - Build the package from source instead of downloading and installing
            a binary. Requires that the port source tree is already installed.
            Automatically builds and installs the 'sqlports' package, if it is
            not already installed.
        version_added: "2.1"
    ports_dir:
        required: false
        default: /usr/ports
        description:
          - When used in combination with the 'build' option, allows overriding
            the default ports source directory.
        version_added: "2.1"
'''

EXAMPLES = '''
# Make sure nmap is installed
- openbsd_pkg: name=nmap state=present

# Make sure nmap is the latest version
- openbsd_pkg: name=nmap state=latest

# Make sure nmap is not installed
- openbsd_pkg: name=nmap state=absent

# Make sure nmap is installed, build it from source if it is not
- openbsd_pkg: name=nmap state=present build=yes

# Specify a pkg flavour with '--'
- openbsd_pkg: name=vim--no_x11 state=present

# Specify the default flavour to avoid ambiguity errors
- openbsd_pkg: name=vim-- state=present

# Update all packages on the system
- openbsd_pkg: name=* state=latest
'''

# Function used for executing commands.
def execute_command(cmd, module):
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

    module.debug("get_current_name(): pattern = %s" % pattern)

    for line in stdout.splitlines():
        module.debug("get_current_name: line = %s" % line)
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
    build = module.params['build']

    if module.check_mode:
        install_cmd = 'pkg_add -Imn'
    else:
        if build is True:
            port_dir = "%s/%s" % (module.params['ports_dir'], get_package_source_path(name, pkg_spec, module))
            if os.path.isdir(port_dir):
                if pkg_spec['flavor']:
                    flavors = pkg_spec['flavor'].replace('-', ' ')
                    install_cmd = "cd %s && make clean=depends && FLAVOR=\"%s\" make install && make clean=depends" % (port_dir, flavors)
                elif pkg_spec['subpackage']:
                    install_cmd = "cd %s && make clean=depends && SUBPACKAGE=\"%s\" make install && make clean=depends" % (port_dir, pkg_spec['subpackage'])
                else:
                    install_cmd = "cd %s && make install && make clean=depends" % (port_dir)
            else:
                module.fail_json(msg="the port source directory %s does not exist" % (port_dir))
        else:
            install_cmd = 'pkg_add -Im'

    if installed_state is False:

        # Attempt to install the package
        if build is True and not module.check_mode:
            (rc, stdout, stderr) = module.run_command(install_cmd, module, use_unsafe_shell=True)
        else:
            (rc, stdout, stderr) = execute_command("%s %s" % (install_cmd, name), module)

        # The behaviour of pkg_add is a bit different depending on if a
        # specific version is supplied or not.
        #
        # When a specific version is supplied the return code will be 0 when
        # a package is found and 1 when it is not, if a version is not
        # supplied the tool will exit 0 in both cases:
        if pkg_spec['version'] or build is True:
            # Depend on the return code.
            module.debug("package_present(): depending on return code")
            if rc:
                changed=False
        else:
            # Depend on stderr instead.
            module.debug("package_present(): depending on stderr")
            if stderr:
                # There is a corner case where having an empty directory in
                # installpath prior to the right location will result in a
                # "file:/local/package/directory/ is empty" message on stderr
                # while still installing the package, so we need to look for
                # for a message like "packagename-1.0: ok" just in case.
                match = re.search("\W%s-[^:]+: ok\W" % name, stdout)
                if match:
                    # It turns out we were able to install the package.
                    module.debug("package_present(): we were able to install package")
                    pass
                else:
                    # We really did fail, fake the return code.
                    module.debug("package_present(): we really did fail")
                    rc = 1
                    changed=False
            else:
                module.debug("package_present(): stderr was not set")

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

    if module.params['build'] is True:
        module.fail_json(msg="the combination of build=%s and state=latest is not supported" % module.params['build'])

    if module.check_mode:
        upgrade_cmd = 'pkg_add -umn'
    else:
        upgrade_cmd = 'pkg_add -um'

    pre_upgrade_name = ''

    if installed_state is True:

        # Fetch name of currently installed package.
        pre_upgrade_name = get_current_name(name, pkg_spec, module)

        module.debug("package_latest(): pre_upgrade_name = %s" % pre_upgrade_name)

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
        module.debug("package_latest(): package is not installed, calling package_present()")
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
            pkg_spec['style']             = 'version'
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
            pkg_spec['style']             = 'versionless'
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
            pkg_spec['style']             = 'stem'
        else:
            module.fail_json(msg="Unable to parse package name at else: " + name)

    # Sanity check that there are no trailing dashes in flavor.
    # Try to stop strange stuff early so we can be strict later.
    if pkg_spec['flavor']:
        match = re.search("-$", pkg_spec['flavor'])
        if match:
            module.fail_json(msg="Trailing dash in flavor: " + pkg_spec['flavor'])

# Function used for figuring out the port path.
def get_package_source_path(name, pkg_spec, module):
    pkg_spec['subpackage'] = None
    if pkg_spec['stem'] == 'sqlports':
        return 'databases/sqlports'
    else:
        # try for an exact match first
        conn = sqlite3.connect('/usr/local/share/sqlports')
        first_part_of_query = 'SELECT fullpkgpath, fullpkgname FROM ports WHERE fullpkgname'
        query = first_part_of_query + ' = ?'
        cursor = conn.execute(query, (name,))
        results = cursor.fetchall()

        # next, try for a fuzzier match
        if len(results) < 1:
            looking_for = pkg_spec['stem'] + (pkg_spec['version_separator'] or '-') + (pkg_spec['version'] or '%')
            query = first_part_of_query + ' LIKE ?'
            if pkg_spec['flavor']:
                looking_for += pkg_spec['flavor_separator'] + pkg_spec['flavor']
                cursor = conn.execute(query, (looking_for,))
            elif pkg_spec['style'] == 'versionless':
                query += ' AND fullpkgname NOT LIKE ?'
                cursor = conn.execute(query, (looking_for, "%s-%%" % looking_for,))
            else:
                cursor = conn.execute(query, (looking_for,))
            results = cursor.fetchall()

        # error if we don't find exactly 1 match
        conn.close()
        if len(results) < 1:
            module.fail_json(msg="could not find a port by the name '%s'" % name)
        if len(results) > 1:
            matches = map(lambda x:x[1], results)
            module.fail_json(msg="too many matches, unsure which to build: %s" % ' OR '.join(matches))

        # there's exactly 1 match, so figure out the subpackage, if any, then return
        fullpkgpath = results[0][0]
        parts = fullpkgpath.split(',')
        if len(parts) > 1 and parts[1][0] == '-':
            pkg_spec['subpackage'] = parts[1]
        return parts[0]

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
            build = dict(default='no', type='bool'),
            ports_dir = dict(default='/usr/ports'),
        ),
        supports_check_mode = True
    )

    name      = module.params['name']
    state     = module.params['state']
    build     = module.params['build']
    ports_dir = module.params['ports_dir']

    rc = 0
    stdout = ''
    stderr = ''
    result = {}
    result['name'] = name
    result['state'] = state
    result['build'] = build

    if build is True:
        if not os.path.isdir(ports_dir):
            module.fail_json(msg="the ports source directory %s does not exist" % (ports_dir))

        # build sqlports if its not installed yet
        pkg_spec = {}
        parse_package_name('sqlports', pkg_spec, module)
        installed_state = get_package_state(name, pkg_spec, module)
        if not installed_state:
            package_present('sqlports', installed_state, pkg_spec, module)

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
