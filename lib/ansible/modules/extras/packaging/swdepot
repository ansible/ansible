#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2013, Raul Melo
# Written by Raul Melo <raulmelo@gmail.com>
# Based on yum module written by Seth Vidal <skvidal at fedoraproject.org>
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

import re
import pipes

DOCUMENTATION = '''
---
module: swdepot
short_description: Manage packages with swdepot package manager (HP-UX)
description:
    - Will install, upgrade and remove packages with swdepot package manager (HP-UX)
version_added: "1.4"
notes: []
author: Raul Melo
options:
    name:
        description:
            - package name.
        required: true
        default: null
        choices: []
        aliases: []
        version_added: 1.4
    state:
        description:
            - whether to install (C(present), C(latest)), or remove (C(absent)) a package.
        required: true
        default: null
        choices: [ 'present', 'latest', 'absent']
        aliases: []
        version_added: 1.4
    depot:
        description:
            - The source repository from which install or upgrade a package.
        required: false
        default: null
        choices: []
        aliases: []
        version_added: 1.4
'''

EXAMPLES = '''
- swdepot: name=unzip-6.0 state=installed depot=repository:/path
- swdepot: name=unzip state=latest depot=repository:/path
- swdepot: name=unzip state=absent
'''

def compare_package(version1, version2):
    """ Compare version packages.
        Return values:
        -1 first minor
        0 equal
        1 fisrt greater """

    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(version1), normalize(version2))

def query_package(module, name, depot=None):
    """ Returns whether a package is installed or not and version. """

    cmd_list = '/usr/sbin/swlist -a revision -l product'
    if depot:
        rc, stdout, stderr = module.run_command("%s -s %s %s | grep %s" % (cmd_list, pipes.quote(depot), pipes.quote(name), pipes.quote(name)), use_unsafe_shell=True)
    else:
        rc, stdout, stderr = module.run_command("%s %s | grep %s" % (cmd_list, pipes.quote(name), pipes.quote(name)), use_unsafe_shell=True)
    if rc == 0:
        version = re.sub("\s\s+|\t" , " ", stdout).strip().split()[1]
    else:
        version = None

    return rc, version

def remove_package(module, name):
    """ Uninstall package if installed. """

    cmd_remove = '/usr/sbin/swremove'
    rc, stdout, stderr = module.run_command("%s %s" % (cmd_remove, name))

    if rc == 0:
        return rc, stdout
    else:
        return rc, stderr

def install_package(module, depot, name):
    """ Install package if not already installed """

    cmd_install = '/usr/sbin/swinstall -x mount_all_filesystems=false'
    rc, stdout, stderr = module.run_command("%s -s %s %s" % (cmd_install, depot, name))
    if rc == 0:
        return rc, stdout
    else:
        return rc, stderr

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(aliases=['pkg'], required=True),
            state = dict(choices=['present', 'absent', 'latest'], required=True),
            depot = dict(default=None, required=False)
        ),
        supports_check_mode=True
    )
    name = module.params['name']
    state = module.params['state']
    depot = module.params['depot']

    changed = False
    msg = "No changed"
    rc = 0
    if ( state == 'present' or state == 'latest' ) and depot == None:
        output = "depot parameter is mandatory in present or latest task"
        module.fail_json(name=name, msg=output, rc=rc)


    #Check local version
    rc, version_installed = query_package(module, name)
    if not rc:
        installed = True
        msg = "Already installed"

    else:
        installed = False

    if ( state == 'present' or state == 'latest' ) and installed == False:
        if module.check_mode:
            module.exit_json(changed=True)
        rc, output = install_package(module, depot, name)

        if not rc:
            changed = True
            msg = "Packaged installed"

        else:
            module.fail_json(name=name, msg=output, rc=rc)

    elif state == 'latest' and installed == True:
        #Check depot version
        rc, version_depot = query_package(module, name, depot)

        if not rc:
            if compare_package(version_installed,version_depot) == -1:
                if module.check_mode:
                    module.exit_json(changed=True)
                #Install new version
                rc, output = install_package(module, depot, name)

                if not rc:
                    msg = "Packge upgraded, Before " + version_installed + " Now " + version_depot
                    changed = True

                else:
                    module.fail_json(name=name, msg=output, rc=rc)

        else:
            output = "Software package not in repository " + depot
            module.fail_json(name=name, msg=output, rc=rc)

    elif state == 'absent' and installed == True:
        if module.check_mode:
            module.exit_json(changed=True)
        rc, output = remove_package(module, name)
        if not rc:
            changed = True
            msg = "Package removed"
        else:
            module.fail_json(name=name, msg=output, rc=rc)

    if module.check_mode:
        module.exit_json(changed=False)

    module.exit_json(changed=changed, name=name, state=state, msg=msg)

# import module snippets
from ansible.module_utils.basic import *

main()

