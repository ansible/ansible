#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrik Lundin <patrik@sigterm.se>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
    clean:
        required: false
        choices: [ yes, no ]
        default: no
        description:
          - When updating or removing packages, delete the extra configuration
            file(s) in the old packages which are annotated with @extra in
            the packaging-list.
        version_added: "2.3"
    quick:
        required: false
        choices: [ yes, no ]
        default: no
        description:
          - Replace or delete packages quickly; do not bother with checksums
            before removing normal files.
        version_added: "2.3"
'''

EXAMPLES = '''
# Make sure nmap is installed
- openbsd_pkg:
    name: nmap
    state: present

# Make sure nmap is the latest version
- openbsd_pkg:
    name: nmap
    state: latest

# Make sure nmap is not installed
- openbsd_pkg:
    name: nmap
    state: absent

# Make sure nmap is installed, build it from source if it is not
- openbsd_pkg:
    name: nmap
    state: present
    build: yes

# Specify a pkg flavour with '--'
- openbsd_pkg:
    name: vim--no_x11
    state: present

# Specify the default flavour to avoid ambiguity errors
- openbsd_pkg:
    name: vim--
    state: present

# Specify a package branch (requires at least OpenBSD 6.0)
- openbsd_pkg:
    name: python%3.5
    state: present

# Update all packages on the system
- openbsd_pkg:
    name: '*'
    state: latest

# Purge a package and it's configuration files
- openbsd_pkg: name=mpd clean=yes state=absent

# Quickly remove a package without checking checksums
- openbsd_pkg: name=qt5 quick=yes state=absent
'''

import os
import platform
import re
import shlex
import sqlite3

from distutils.version import StrictVersion


# Function used for executing commands.
def execute_command(cmd, module):
    # Break command line into arguments.
    # This makes run_command() use shell=False which we need to not cause shell
    # expansion of special characters like '*'.
    cmd_args = shlex.split(cmd)
    return module.run_command(cmd_args)

# Function used to find out if a package is currently installed.
def get_package_state(names, pkg_spec, module):
    info_cmd = 'pkg_info -Iq'

    for name in names:
        command = "%s inst:%s" % (info_cmd, name)

        rc, stdout, stderr = execute_command(command, module)

        if stderr:
            module.fail_json(msg="failed in get_package_state(): " + stderr)

        if stdout:
            # If the requested package name is just a stem, like "python", we may
            # find multiple packages with that name.
            pkg_spec[name]['installed_names'] = [installed_name for installed_name in stdout.splitlines()]
            module.debug("get_package_state(): installed_names = %s" % pkg_spec[name]['installed_names'])
            pkg_spec[name]['installed_state'] = True
        else:
            pkg_spec[name]['installed_state'] = False

# Function used to make sure a package is present.
def package_present(names, pkg_spec, module):
    build = module.params['build']

    for name in names:
        # It is possible package_present() has been called from package_latest().
        # In that case we do not want to operate on the whole list of names,
        # only the leftovers.
        if pkg_spec['package_latest_leftovers']:
            if name not in pkg_spec['package_latest_leftovers']:
                module.debug("package_present(): ignoring '%s' which is not a package_latest() leftover" % name)
                continue
            else:
                module.debug("package_present(): handling package_latest() leftovers, installing '%s'" % name)

        if module.check_mode:
            install_cmd = 'pkg_add -Imn'
        else:
            if build is True:
                port_dir = "%s/%s" % (module.params['ports_dir'], get_package_source_path(name, pkg_spec, module))
                if os.path.isdir(port_dir):
                    if pkg_spec[name]['flavor']:
                        flavors = pkg_spec[name]['flavor'].replace('-', ' ')
                        install_cmd = "cd %s && make clean=depends && FLAVOR=\"%s\" make install && make clean=depends" % (port_dir, flavors)
                    elif pkg_spec[name]['subpackage']:
                        install_cmd = "cd %s && make clean=depends && SUBPACKAGE=\"%s\" make install && make clean=depends" % (port_dir,
                                                                                                                               pkg_spec[name]['subpackage'])
                    else:
                        install_cmd = "cd %s && make install && make clean=depends" % (port_dir)
                else:
                    module.fail_json(msg="the port source directory %s does not exist" % (port_dir))
            else:
                install_cmd = 'pkg_add -Im'

        if pkg_spec[name]['installed_state'] is False:

            # Attempt to install the package
            if build is True and not module.check_mode:
                (pkg_spec[name]['rc'], pkg_spec[name]['stdout'], pkg_spec[name]['stderr']) = module.run_command(install_cmd, module, use_unsafe_shell=True)
            else:
                (pkg_spec[name]['rc'], pkg_spec[name]['stdout'], pkg_spec[name]['stderr']) = execute_command("%s %s" % (install_cmd, name), module)

            # The behaviour of pkg_add is a bit different depending on if a
            # specific version is supplied or not.
            #
            # When a specific version is supplied the return code will be 0 when
            # a package is found and 1 when it is not. If a version is not
            # supplied the tool will exit 0 in both cases.
            #
            # It is important to note that "version" relates to the
            # packages-specs(7) notion of a version. If using the branch syntax
            # (like "python%3.5") even though a branch name may look like a
            # version string it is not used an one by pkg_add.
            if pkg_spec[name]['version'] or build is True:
                # Depend on the return code.
                module.debug("package_present(): depending on return code for name '%s'" % name)
                if pkg_spec[name]['rc']:
                    pkg_spec[name]['changed'] = False
            else:
                # Depend on stderr instead.
                module.debug("package_present(): depending on stderr for name '%s'" % name)
                if pkg_spec[name]['stderr']:
                    # There is a corner case where having an empty directory in
                    # installpath prior to the right location will result in a
                    # "file:/local/package/directory/ is empty" message on stderr
                    # while still installing the package, so we need to look for
                    # for a message like "packagename-1.0: ok" just in case.
                    match = re.search("\W%s-[^:]+: ok\W" % pkg_spec[name]['stem'], pkg_spec[name]['stdout'])

                    if match:
                        # It turns out we were able to install the package.
                        module.debug("package_present(): we were able to install package for name '%s'" % name)
                    else:
                        # We really did fail, fake the return code.
                        module.debug("package_present(): we really did fail for name '%s'" % name)
                        pkg_spec[name]['rc'] = 1
                        pkg_spec[name]['changed'] = False
                else:
                    module.debug("package_present(): stderr was not set for name '%s'" % name)

            if pkg_spec[name]['rc'] == 0:
                pkg_spec[name]['changed'] = True

        else:
            pkg_spec[name]['rc'] = 0
            pkg_spec[name]['stdout'] = ''
            pkg_spec[name]['stderr'] = ''
            pkg_spec[name]['changed'] = False

# Function used to make sure a package is the latest available version.
def package_latest(names, pkg_spec, module):
    if module.params['build'] is True:
        module.fail_json(msg="the combination of build=%s and state=latest is not supported" % module.params['build'])

    upgrade_cmd = 'pkg_add -um'

    if module.check_mode:
        upgrade_cmd += 'n'

    if module.params['clean']:
        upgrade_cmd += 'c'

    if module.params['quick']:
        upgrade_cmd += 'q'

    for name in names:
        if pkg_spec[name]['installed_state'] is True:

            # Attempt to upgrade the package.
            (pkg_spec[name]['rc'], pkg_spec[name]['stdout'], pkg_spec[name]['stderr']) = execute_command("%s %s" % (upgrade_cmd, name), module)

            # Look for output looking something like "nmap-6.01->6.25: ok" to see if
            # something changed (or would have changed). Use \W to delimit the match
            # from progress meter output.
            pkg_spec[name]['changed'] = False
            for installed_name in pkg_spec[name]['installed_names']:
                module.debug("package_latest(): checking for pre-upgrade package name: %s" % installed_name)
                match = re.search("\W%s->.+: ok\W" % installed_name, pkg_spec[name]['stdout'])
                if match:
                    module.debug("package_latest(): pre-upgrade package name match: %s" % installed_name)

                    pkg_spec[name]['changed'] = True
                    break

            # FIXME: This part is problematic. Based on the issues mentioned (and
            # handled) in package_present() it is not safe to blindly trust stderr
            # as an indicator that the command failed, and in the case with
            # empty installpath directories this will break.
            #
            # For now keep this safeguard here, but ignore it if we managed to
            # parse out a successful update above. This way we will report a
            # successful run when we actually modify something but fail
            # otherwise.
            if pkg_spec[name]['changed'] is not True:
                if pkg_spec[name]['stderr']:
                    pkg_spec[name]['rc'] = 1

        else:
            # Note packages that need to be handled by package_present
            module.debug("package_latest(): package '%s' is not installed, will be handled by package_present()" % name)
            pkg_spec['package_latest_leftovers'].append(name)

    # If there were any packages that were not installed we call
    # package_present() which will handle those.
    if pkg_spec['package_latest_leftovers']:
        module.debug("package_latest(): calling package_present() to handle leftovers")
        package_present(names, pkg_spec, module)

# Function used to make sure a package is not installed.
def package_absent(names, pkg_spec, module):
    remove_cmd = 'pkg_delete -I'

    if module.check_mode:
        remove_cmd += 'n'

    if module.params['clean']:
        remove_cmd += 'c'

    if module.params['quick']:
        remove_cmd += 'q'

    for name in names:
        if pkg_spec[name]['installed_state'] is True:
            # Attempt to remove the package.
            (pkg_spec[name]['rc'], pkg_spec[name]['stdout'], pkg_spec[name]['stderr']) = execute_command("%s %s" % (remove_cmd, name), module)

            if pkg_spec[name]['rc'] == 0:
                pkg_spec[name]['changed'] = True
            else:
                pkg_spec[name]['changed'] = False

        else:
            pkg_spec[name]['rc'] = 0
            pkg_spec[name]['stdout'] = ''
            pkg_spec[name]['stderr'] = ''
            pkg_spec[name]['changed'] = False

# Function used to parse the package name based on packages-specs(7).
# The general name structure is "stem-version[-flavors]".
#
# Names containing "%" are a special variation not part of the
# packages-specs(7) syntax. See pkg_add(1) on OpenBSD 6.0 or later for a
# description.
def parse_package_name(names, pkg_spec, module):

    # Initialize empty list of package_latest() leftovers.
    pkg_spec['package_latest_leftovers'] = []

    for name in names:
        module.debug("parse_package_name(): parsing name: %s" % name)
        # Do some initial matches so we can base the more advanced regex on that.
        version_match = re.search("-[0-9]", name)
        versionless_match = re.search("--", name)

        # Stop if someone is giving us a name that both has a version and is
        # version-less at the same time.
        if version_match and versionless_match:
            module.fail_json(msg="package name both has a version and is version-less: " + name)

        # All information for a given name is kept in the pkg_spec keyed by that name.
        pkg_spec[name] = {}

        # If name includes a version.
        if version_match:
            match = re.search("^(?P<stem>[^%]+)-(?P<version>[0-9][^-]*)(?P<flavor_separator>-)?(?P<flavor>[a-z].*)?(%(?P<branch>.+))?$", name)
            if match:
                pkg_spec[name]['stem']              = match.group('stem')
                pkg_spec[name]['version_separator'] = '-'
                pkg_spec[name]['version']           = match.group('version')
                pkg_spec[name]['flavor_separator']  = match.group('flavor_separator')
                pkg_spec[name]['flavor']            = match.group('flavor')
                pkg_spec[name]['branch']            = match.group('branch')
                pkg_spec[name]['style']             = 'version'
                module.debug("version_match: stem: %s, version: %s, flavor_separator: %s, flavor: %s, branch: %s, style: %s" %
                    (
                        pkg_spec[name]['stem'],
                        pkg_spec[name]['version'],
                        pkg_spec[name]['flavor_separator'],
                        pkg_spec[name]['flavor'],
                        pkg_spec[name]['branch'],
                        pkg_spec[name]['style']
                    )
                )
            else:
                module.fail_json(msg="unable to parse package name at version_match: " + name)

        # If name includes no version but is version-less ("--").
        elif versionless_match:
            match = re.search("^(?P<stem>[^%]+)--(?P<flavor>[a-z].*)?(%(?P<branch>.+))?$", name)
            if match:
                pkg_spec[name]['stem']              = match.group('stem')
                pkg_spec[name]['version_separator'] = '-'
                pkg_spec[name]['version']           = None
                pkg_spec[name]['flavor_separator']  = '-'
                pkg_spec[name]['flavor']            = match.group('flavor')
                pkg_spec[name]['branch']            = match.group('branch')
                pkg_spec[name]['style']             = 'versionless'
                module.debug("versionless_match: stem: %s, flavor: %s, branch: %s, style: %s" %
                    (
                        pkg_spec[name]['stem'],
                        pkg_spec[name]['flavor'],
                        pkg_spec[name]['branch'],
                        pkg_spec[name]['style']
                    )
                )
            else:
                module.fail_json(msg="unable to parse package name at versionless_match: " + name)

        # If name includes no version, and is not version-less, it is all a
        # stem, possibly with a branch (%branchname) tacked on at the
        # end.
        else:
            match = re.search("^(?P<stem>[^%]+)(%(?P<branch>.+))?$", name)
            if match:
                pkg_spec[name]['stem']              = match.group('stem')
                pkg_spec[name]['version_separator'] = None
                pkg_spec[name]['version']           = None
                pkg_spec[name]['flavor_separator']  = None
                pkg_spec[name]['flavor']            = None
                pkg_spec[name]['branch']            = match.group('branch')
                pkg_spec[name]['style']             = 'stem'
                module.debug("stem_match: stem: %s, branch: %s, style: %s" %
                    (
                        pkg_spec[name]['stem'],
                        pkg_spec[name]['branch'],
                        pkg_spec[name]['style']
                    )
                )
            else:
                module.fail_json(msg="unable to parse package name at else: " + name)

        # Verify that the managed host is new enough to support branch syntax.
        if pkg_spec[name]['branch']:
            branch_release = "6.0"

            if StrictVersion(platform.release()) < StrictVersion(branch_release):
                module.fail_json(msg="package name using 'branch' syntax requires at least OpenBSD %s: %s" % (branch_release, name))

        # Sanity check that there are no trailing dashes in flavor.
        # Try to stop strange stuff early so we can be strict later.
        if pkg_spec[name]['flavor']:
            match = re.search("-$", pkg_spec[name]['flavor'])
            if match:
                module.fail_json(msg="trailing dash in flavor: " + pkg_spec[name]['flavor'])

# Function used for figuring out the port path.
def get_package_source_path(name, pkg_spec, module):
    pkg_spec[name]['subpackage'] = None
    if pkg_spec[name]['stem'] == 'sqlports':
        return 'databases/sqlports'
    else:
        # try for an exact match first
        sqlports_db_file = '/usr/local/share/sqlports'
        if not os.path.isfile(sqlports_db_file):
            module.fail_json(msg="sqlports file '%s' is missing" % sqlports_db_file)

        conn = sqlite3.connect(sqlports_db_file)
        first_part_of_query = 'SELECT fullpkgpath, fullpkgname FROM ports WHERE fullpkgname'
        query = first_part_of_query + ' = ?'
        module.debug("package_package_source_path(): exact query: %s" % query)
        cursor = conn.execute(query, (name,))
        results = cursor.fetchall()

        # next, try for a fuzzier match
        if len(results) < 1:
            looking_for = pkg_spec[name]['stem'] + (pkg_spec[name]['version_separator'] or '-') + (pkg_spec[name]['version'] or '%')
            query = first_part_of_query + ' LIKE ?'
            if pkg_spec[name]['flavor']:
                looking_for += pkg_spec[name]['flavor_separator'] + pkg_spec[name]['flavor']
                module.debug("package_package_source_path(): fuzzy flavor query: %s" % query)
                cursor = conn.execute(query, (looking_for,))
            elif pkg_spec[name]['style'] == 'versionless':
                query += ' AND fullpkgname NOT LIKE ?'
                module.debug("package_package_source_path(): fuzzy versionless query: %s" % query)
                cursor = conn.execute(query, (looking_for, "%s-%%" % looking_for,))
            else:
                module.debug("package_package_source_path(): fuzzy query: %s" % query)
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
            pkg_spec[name]['subpackage'] = parts[1]
        return parts[0]

# Function used for upgrading all installed packages.
def upgrade_packages(pkg_spec, module):
    if module.check_mode:
        upgrade_cmd = 'pkg_add -Imnu'
    else:
        upgrade_cmd = 'pkg_add -Imu'

    # Create a minimal pkg_spec entry for '*' to store return values.
    pkg_spec['*'] = {}

    # Attempt to upgrade all packages.
    pkg_spec['*']['rc'], pkg_spec['*']['stdout'], pkg_spec['*']['stderr'] = execute_command("%s" % upgrade_cmd, module)

    # Try to find any occurrence of a package changing version like:
    # "bzip2-1.0.6->1.0.6p0: ok".
    match = re.search("\W\w.+->.+: ok\W", pkg_spec['*']['stdout'])
    if match:
        pkg_spec['*']['changed'] = True

    else:
        pkg_spec['*']['changed'] = False

    # It seems we can not trust the return value, so depend on the presence of
    # stderr to know if something failed.
    if pkg_spec['*']['stderr']:
        pkg_spec['*']['rc'] = 1
    else:
        pkg_spec['*']['rc'] = 0

# ===========================================
# Main control flow.

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, type='list'),
            state = dict(required=True, choices=['absent', 'installed', 'latest', 'present', 'removed']),
            build = dict(default='no', type='bool'),
            ports_dir = dict(default='/usr/ports'),
            quick = dict(default='no', type='bool'),
            clean = dict(default='no', type='bool')
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

    # The data structure used to keep track of package information.
    pkg_spec = {}

    if build is True:
        if not os.path.isdir(ports_dir):
            module.fail_json(msg="the ports source directory %s does not exist" % (ports_dir))

        # build sqlports if its not installed yet
        parse_package_name(['sqlports'], pkg_spec, module)
        get_package_state(['sqlports'], pkg_spec, module)
        if not pkg_spec['sqlports']['installed_state']:
            module.debug("main(): installing 'sqlports' because build=%s" % module.params['build'])
            package_present(['sqlports'], pkg_spec, module)

    asterisk_name = False
    for n in name:
        if n == '*':
            if len(name) != 1:
                module.fail_json(msg="the package name '*' can not be mixed with other names")

            asterisk_name = True

    if asterisk_name:
        if state != 'latest':
            module.fail_json(msg="the package name '*' is only valid when using state=latest")
        else:
            # Perform an upgrade of all installed packages.
            upgrade_packages(pkg_spec, module)
    else:
        # Parse package names and put results in the pkg_spec dictionary.
        parse_package_name(name, pkg_spec, module)

        # Not sure how the branch syntax is supposed to play together
        # with build mode. Disable it for now.
        for n in name:
            if pkg_spec[n]['branch'] and module.params['build'] is True:
                module.fail_json(msg="the combination of 'branch' syntax and build=%s is not supported: %s" % (module.params['build'], n))

        # Get state for all package names.
        get_package_state(name, pkg_spec, module)

        # Perform requested action.
        if state in ['installed', 'present']:
            package_present(name, pkg_spec, module)
        elif state in ['absent', 'removed']:
            package_absent(name, pkg_spec, module)
        elif state == 'latest':
            package_latest(name, pkg_spec, module)

    # The combined changed status for all requested packages. If anything
    # is changed this is set to True.
    combined_changed = False

    # We combine all error messages in this comma separated string, for example:
    # "msg": "Can't find nmapp\n, Can't find nmappp\n"
    combined_error_message = ''

    # Loop over all requested package names and check if anything failed or
    # changed.
    for n in name:
        if pkg_spec[n]['rc'] != 0:
            if pkg_spec[n]['stderr']:
                if combined_error_message:
                    combined_error_message += ", %s" % pkg_spec[n]['stderr']
                else:
                    combined_error_message = pkg_spec[n]['stderr']
            else:
                if combined_error_message:
                    combined_error_message += ", %s" % pkg_spec[n]['stdout']
                else:
                    combined_error_message = pkg_spec[n]['stdout']

        if pkg_spec[n]['changed'] is True:
            combined_changed = True

    # If combined_error_message contains anything at least some part of the
    # list of requested package names failed.
    if combined_error_message:
        module.fail_json(msg=combined_error_message)

    result['changed'] = combined_changed

    module.exit_json(**result)

# Import module snippets.
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
