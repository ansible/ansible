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

from xml.dom.minidom import parseString as parseXML
import re

DOCUMENTATION = '''
---
module: zypper
author:
    - "Patrick Callahan (@dirtyharrycallahan)"
    - "Alexander Gubin (@alxgu)"
    - "Thomas O'Donnell (@andytom)"
    - "Robin Roth (@robinro)"
    - "Andrii Radyk (@AnderEnder)"
version_added: "1.2"
short_description: Manage packages on SUSE and openSUSE
description:
    - Manage packages on SUSE and openSUSE using the zypper and rpm tools.
options:
    name:
        description:
        - Package name C(name) or package specifier.
        - Can include a version like C(name=1.0), C(name>3.4) or C(name<=2.7). If a version is given, C(oldpackage) is implied and zypper is allowed to update the package within the version range given.
        - You can also pass a url or a local path to a rpm file.
        - When using state=latest, this can be '*', which updates all installed packages.
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
        choices: [ package, patch, pattern, product, srcpackage, application ]
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
    disable_recommends:
        version_added: "1.8"
        description:
          - Corresponds to the C(--no-recommends) option for I(zypper). Default behavior (C(yes)) modifies zypper's default behavior; C(no) does install recommended packages.
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
    force:
        version_added: "2.2"
        description:
          - Adds C(--force) option to I(zypper). Allows to downgrade packages and change vendor or architecture.
        required: false
        default: "no"
        choices: [ "yes", "no" ]
    update_cache:
        version_added: "2.2"
        description:
          - Run the equivalent of C(zypper refresh) before the operation.
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        aliases: [ "refresh" ]
    oldpackage:
        version_added: "2.2"
        description:
          - Adds C(--oldpackage) option to I(zypper). Allows to downgrade packages with less side-effects than force. This is implied as soon as a version is specified as part of the package name.
        required: false
        default: "no"
        choices: [ "yes", "no" ]

# informational: requirements for nodes
requirements:
    - "zypper >= 1.0  # included in openSuSE >= 11.1 or SuSE Linux Enterprise Server/Desktop >= 11.0"
    - python-xml
    - rpm
'''

EXAMPLES = '''
# Install "nmap"
- zypper: name=nmap state=present

# Install apache2 with recommended packages
- zypper: name=apache2 state=present disable_recommends=no

# Apply a given patch
- zypper: name=openSUSE-2016-128 state=present type=patch

# Remove the "nmap" package
- zypper: name=nmap state=absent

# Install the nginx rpm from a remote repo
- zypper: name=http://nginx.org/packages/sles/12/x86_64/RPMS/nginx-1.8.0-1.sles12.ngx.x86_64.rpm state=present

# Install local rpm file
- zypper: name=/tmp/fancy-software.rpm state=present

# Update all packages
- zypper: name=* state=latest

# Apply all available patches
- zypper: name=* state=latest type=patch

# Refresh repositories and update package "openssl"
- zypper: name=openssl state=present update_cache=yes

# Install specific version (possible comparisons: <, >, <=, >=, =)
- zypper: name=docker>=1.10 state=installed
'''


def split_name_version(name):
    """splits of the package name and desired version

    example formats:
        - docker>=1.10
        - apache=2.4

    Allowed version specifiers: <, >, <=, >=, =
    Allowed version format: [0-9.-]*

    Also allows a prefix indicating remove "-", "~" or install "+"
    """

    prefix = ''
    if name[0] in ['-', '~', '+']:
        prefix = name[0]
        name = name[1:]

    version_check = re.compile('^(.*?)((?:<|>|<=|>=|=)[0-9.-]*)?$')
    try:
        reres = version_check.match(name)
        name, version = reres.groups()
        return prefix, name, version
    except:
        return prefix, name, None


def get_want_state(m, names, remove=False):
    packages_install = {}
    packages_remove = {}
    urls = []
    for name in names:
        if '://' in name or name.endswith('.rpm'):
            urls.append(name)
        else:
            prefix, pname, version = split_name_version(name)
            if prefix in ['-', '~']:
                packages_remove[pname] = version
            elif prefix == '+':
                packages_install[pname] = version
            else:
                if remove:
                    packages_remove[pname] = version
                else:
                    packages_install[pname] = version
    return packages_install, packages_remove, urls


def get_installed_state(m, packages):
    "get installed state of packages"

    cmd = get_cmd(m, 'search')
    cmd.extend(['--match-exact', '--details', '--installed-only'])
    cmd.extend(packages)
    return parse_zypper_xml(m, cmd, fail_not_found=False)[0]


def parse_zypper_xml(m, cmd, fail_not_found=True, packages=None):
    rc, stdout, stderr = m.run_command(cmd, check_rc=False)

    dom = parseXML(stdout)
    if rc == 104:
        # exit code 104 is ZYPPER_EXIT_INF_CAP_NOT_FOUND (no packages found)
        if fail_not_found:
            errmsg = dom.getElementsByTagName('message')[-1].childNodes[0].data
            m.fail_json(msg=errmsg, rc=rc, stdout=stdout, stderr=stderr, cmd=cmd)
        else:
            return {}, rc, stdout, stderr
    elif rc in [0, 106, 103]:
        # zypper exit codes
        # 0: success
        # 106: signature verification failed
        # 103: zypper was upgraded, run same command again
        if packages is None:
            firstrun = True
            packages = {}
        solvable_list = dom.getElementsByTagName('solvable')
        for solvable in solvable_list:
            name = solvable.getAttribute('name')
            packages[name] = {}
            packages[name]['version'] = solvable.getAttribute('edition')
            packages[name]['oldversion'] = solvable.getAttribute('edition-old')
            status = solvable.getAttribute('status')
            packages[name]['installed'] = status == "installed"
            packages[name]['group'] = solvable.parentNode.nodeName
        if rc == 103 and firstrun:
            # if this was the first run and it failed with 103
            # run zypper again with the same command to complete update
            return parse_zypper_xml(m, cmd, fail_not_found=fail_not_found, packages=packages)

        return packages, rc, stdout, stderr
    m.fail_json(msg='Zypper run command failed with return code %s.'%rc, rc=rc, stdout=stdout, stderr=stderr, cmd=cmd)


def get_cmd(m, subcommand):
    "puts together the basic zypper command arguments with those passed to the module"
    is_install = subcommand in ['install', 'update', 'patch']
    is_refresh = subcommand == 'refresh'
    cmd = ['/usr/bin/zypper', '--quiet', '--non-interactive', '--xmlout']

    # add global options before zypper command
    if (is_install or is_refresh) and m.params['disable_gpg_check']:
        cmd.append('--no-gpg-checks')

    cmd.append(subcommand)
    if subcommand != 'patch' and not is_refresh:
        cmd.extend(['--type', m.params['type']])
    if m.check_mode and subcommand != 'search':
        cmd.append('--dry-run')
    if is_install:
        cmd.append('--auto-agree-with-licenses')
        if m.params['disable_recommends']:
            cmd.append('--no-recommends')
        if m.params['force']:
            cmd.append('--force')
        if m.params['oldpackage']:
            cmd.append('--oldpackage')
    return cmd


def set_diff(m, retvals, result):
    # TODO: if there is only one package, set before/after to version numbers
    packages = {'installed': [], 'removed': [], 'upgraded': []}
    if result:
        for p in result:
            group = result[p]['group']
            if group == 'to-upgrade':
                versions = ' (' + result[p]['oldversion'] + ' => ' + result[p]['version'] + ')'
                packages['upgraded'].append(p + versions)
            elif group == 'to-install':
                packages['installed'].append(p)
            elif group == 'to-remove':
                packages['removed'].append(p)

    output = ''
    for state in packages:
        if packages[state]:
            output += state + ': ' + ', '.join(packages[state]) + '\n'
    if 'diff' not in retvals:
        retvals['diff'] = {}
    if 'prepared' not in retvals['diff']:
        retvals['diff']['prepared'] = output
    else:
        retvals['diff']['prepared'] += '\n' + output


def package_present(m, name, want_latest):
    "install and update (if want_latest) the packages in name_install, while removing the packages in name_remove"
    retvals = {'rc': 0, 'stdout': '', 'stderr': ''}
    name_install, name_remove, urls = get_want_state(m, name)

    # if a version string is given, pass it to zypper
    install_version = [p+name_install[p] for p in name_install if name_install[p]]
    remove_version = [p+name_remove[p] for p in name_remove if name_remove[p]]

    # add oldpackage flag when a version is given to allow downgrades
    if install_version or remove_version:
        m.params['oldpackage'] = True

    if not want_latest:
        # for state=present: filter out already installed packages
        install_and_remove = name_install.copy()
        install_and_remove.update(name_remove)
        prerun_state = get_installed_state(m, install_and_remove)
        # generate lists of packages to install or remove
        name_install = [p for p in name_install if p not in prerun_state]
        name_remove = [p for p in name_remove if p in prerun_state]
        if not any((name_install, name_remove, urls, install_version, remove_version)):
            # nothing to install/remove and nothing to update
            return None, retvals

    # zypper install also updates packages
    cmd = get_cmd(m, 'install')
    cmd.append('--')
    cmd.extend(urls)

    # pass packages with version information
    cmd.extend(install_version)
    cmd.extend(['-%s' % p for p in remove_version])

    # allow for + or - prefixes in install/remove lists
    # do this in one zypper run to allow for dependency-resolution
    # for example "-exim postfix" runs without removing packages depending on mailserver
    cmd.extend(name_install)
    cmd.extend(['-%s' % p for p in name_remove])

    retvals['cmd'] = cmd
    result, retvals['rc'], retvals['stdout'], retvals['stderr'] = parse_zypper_xml(m, cmd)

    return result, retvals


def package_update_all(m):
    "run update or patch on all available packages"
    
    retvals = {'rc': 0, 'stdout': '', 'stderr': ''}
    if m.params['type'] == 'patch':
        cmdname = 'patch'
    else:
        cmdname = 'update'

    cmd = get_cmd(m, cmdname)
    retvals['cmd'] = cmd
    result, retvals['rc'], retvals['stdout'], retvals['stderr'] = parse_zypper_xml(m, cmd)
    return result, retvals


def package_absent(m, name):
    "remove the packages in name"
    retvals = {'rc': 0, 'stdout': '', 'stderr': ''}
    # Get package state
    name_install, name_remove, urls = get_want_state(m, name, remove=True)
    if name_install:
        m.fail_json(msg="Can not combine '+' prefix with state=remove/absent.")
    if urls:
        m.fail_json(msg="Can not remove via URL.")
    if m.params['type'] == 'patch':
        m.fail_json(msg="Can not remove patches.")
    prerun_state = get_installed_state(m, name_remove)
    remove_version = [p+name_remove[p] for p in name_remove if name_remove[p]]
    name_remove = [p for p in name_remove if p in prerun_state]
    if not name_remove and not remove_version:
        return None, retvals

    cmd = get_cmd(m, 'remove')
    cmd.extend(name_remove)
    cmd.extend(remove_version)

    retvals['cmd'] = cmd
    result, retvals['rc'], retvals['stdout'], retvals['stderr'] = parse_zypper_xml(m, cmd)
    return result, retvals


def repo_refresh(m):
    "update the repositories"
    retvals = {'rc': 0, 'stdout': '', 'stderr': ''}

    cmd = get_cmd(m, 'refresh')

    retvals['cmd'] = cmd
    result, retvals['rc'], retvals['stdout'], retvals['stderr'] = parse_zypper_xml(m, cmd)

    return retvals

# ===========================================
# Main control flow

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, aliases=['pkg'], type='list'),
            state = dict(required=False, default='present', choices=['absent', 'installed', 'latest', 'present', 'removed']),
            type = dict(required=False, default='package', choices=['package', 'patch', 'pattern', 'product', 'srcpackage', 'application']),
            disable_gpg_check = dict(required=False, default='no', type='bool'),
            disable_recommends = dict(required=False, default='yes', type='bool'),
            force = dict(required=False, default='no', type='bool'),
            update_cache = dict(required=False, aliases=['refresh'], default='no', type='bool'),
            oldpackage = dict(required=False, default='no', type='bool'),
        ),
        supports_check_mode = True
    )

    name = module.params['name']
    state = module.params['state']
    update_cache = module.params['update_cache']

    # remove empty strings from package list
    name = filter(None, name)

    # Refresh repositories
    if update_cache:
        retvals = repo_refresh(module)

        if retvals['rc'] != 0:
            module.fail_json(msg="Zypper refresh run failed.", **retvals)

    # Perform requested action
    if name == ['*'] and state == 'latest':
        packages_changed, retvals = package_update_all(module)
    else:
        if state in ['absent', 'removed']:
            packages_changed, retvals = package_absent(module, name)
        elif state in ['installed', 'present', 'latest']:
            packages_changed, retvals = package_present(module, name, state == 'latest')

    retvals['changed'] = retvals['rc'] == 0 and bool(packages_changed)

    if module._diff:
        set_diff(module, retvals, packages_changed)

    if retvals['rc'] != 0:
        module.fail_json(msg="Zypper run failed.", **retvals)

    if not retvals['changed']:
        del retvals['stdout']
        del retvals['stderr']

    module.exit_json(name=name, state=state, update_cache=update_cache, **retvals)

# import module snippets
from ansible.module_utils.basic import AnsibleModule
if __name__ == "__main__":
    main()
