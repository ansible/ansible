#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrick Pelletier <pp.pelletier@gmail.com>
# Based on pacman (Afterburn) and pkgin (Shaun Zinck) modules
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: opkg
author: "Patrick Pelletier (@skinp)"
short_description: Package manager for OpenWrt
description:
    - Manages OpenWrt packages
version_added: "1.1"
options:
    name:
        description:
            - name of package to install/remove
        required: false
        default: null
        aliases: [ 'pkg', 'package' ]
    state:
        description:
            - state of the package
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    force:
        description:
            - opkg --force parameter used
        choices: ["", "depends", "maintainer", "reinstall", "overwrite", "downgrade", "space", "postinstall", "remove", "checksum", "removal-of-dependent-packages"]
        required: false
        default: absent
        version_added: "2.0"
    update_cache:
        description:
            - update the package db first
        required: false
        default: "no"
        choices: [ "yes", "no" ]
    ipk:
       description:
         - Path to a .ipk package on the remote machine.
         - If :// in the path, ansible will attempt to download ipk before installing.
       required: false
       version_added: "2.3"
notes:  []
'''
EXAMPLES = '''
- opkg:
    name: foo
    state: present

- opkg:
    name: foo
    state: present
    update_cache: yes

- opkg:
    name: foo
    state: absent

- opkg:
    name: foo,bar
    state: absent

- opkg:
    name: foo
    state: present
    force: overwrite
'''

import pipes

from ansible.module_utils.urls import fetch_url

def update_package_db(module, opkg_path):
    """ Updates packages list. """

    rc, out, err = module.run_command("%s update" % opkg_path)

    if rc != 0:
        module.fail_json(msg="could not update package db")


def query_package(module, opkg_path, name, state="present"):
    """ Returns whether a package is installed or not. """

    if state == "present":

        rc, out, err = module.run_command("%s list-installed | grep -q \"^%s \"" % (pipes.quote(opkg_path), pipes.quote(name)), use_unsafe_shell=True)
        if rc == 0:
            return True

        return False


def query_ipk_info(module, opkg_path, pkg_name):
    """ Returns the package metadata as known by opkg """

    rc, out, err = module.run_command("%s info %s" % (pipes.quote(opkg_path), pipes.quote(pkg_name)), use_unsafe_shell=False)
    if rc == 0:
        info = dict([map(str.strip, line.split(':', 1)) for line in out.splitlines() if ':' in line])
        return info

    return False


def download(module, ipk):
    tempdir = os.path.dirname(__file__)
    package = os.path.join(tempdir, str(ipk.rsplit('/', 1)[1]))
    # When downloading a ipk, how much of the ipk to download before
    # saving to a tempfile (64k)
    BUFSIZE = 65536

    try:
        rsp, info = fetch_url(module, ipk)
        f = open(package, 'w')
        # Read 1kb at a time to save on ram
        while True:
            data = rsp.read(BUFSIZE)

            if data == "":
                break # End of file, break while loop

            f.write(data)
        f.close()
        ipk = package
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failure downloading %s, %s" % (ipk, e))

    return ipk


def remove_packages(module, opkg_path, packages):
    """ Uninstalls one or more packages if installed. """

    p = module.params
    force = p["force"]
    if force:
        force = "--force-%s" % force

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, opkg_path, package):
            continue

        rc, out, err = module.run_command("%s remove %s %s" % (opkg_path, force, package))

        if query_package(module, opkg_path, package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, opkg_path, packages, ipk_install=False):
    """ Installs one or more packages if not already installed. """

    p = module.params
    force = p["force"]
    if force:
        force = "--force-%s" % force

    install_c = 0

    for package in packages:
        if ipk_install:
            if '://' in package:
                package = download(module, package)

            package_metadata = query_ipk_info(module, opkg_path, package)
            package_name = package_metadata['Package']
        else:
            package_name = package
        if query_package(module, opkg_path, package_name):
            continue

        rc, out, err = module.run_command("%s install %s %s" % (opkg_path, force, package))

        if not query_package(module, opkg_path, package_name):
            module.fail_json(msg="failed to install %s: %s" % (package_name, out))

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="installed %s package(s)" % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def main():
    module = AnsibleModule(
        argument_spec = dict(
            package = dict(default=None, aliases=['pkg', 'name'], type='list'),
            ipk = dict(default=None, type='list'),
            state = dict(default="present", choices=["present", "installed", "absent", "removed"]),
            force = dict(default="", choices=["", "depends", "maintainer", "reinstall", "overwrite", "downgrade", "space", "postinstall", "remove", "checksum", "removal-of-dependent-packages"]),
            update_cache = dict(default="no", aliases=["update-cache"], type='bool')
        ),
        mutually_exclusive = [['package', 'ipk']],
        required_one_of = [['package', 'ipk']]
    )

    opkg_path = module.get_bin_path('opkg', True, ['/bin'])

    p = module.params

    if p["update_cache"]:
        update_package_db(module, opkg_path)

    if p['ipk']:
        if p['state'] not in ["present", "installed"]:
            module.fail_json(msg="ipk only supports state=present")
        install_packages(module, opkg_path, p['ipk'], True)
    else:
        if p["state"] in ["present", "installed"]:
            install_packages(module, opkg_path, p["package"])

        elif p["state"] in ["absent", "removed"]:
            remove_packages(module, opkg_path, p["package"])

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
