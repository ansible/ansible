#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Patrick Pelletier <pp.pelletier@gmail.com>
# Based on pacman (Afterburn) and pkgin (Shaun Zinck) modules
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

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
        required: true
    state:
        description:
            - state of the package
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    force:
        description:
            - opkg --force parameter used
        choices:
            - ""
            - "depends"
            - "maintainer"
            - "reinstall"
            - "overwrite"
            - "downgrade"
            - "space"
            - "postinstall"
            - "remove"
            - "checksum"
            - "removal-of-dependent-packages"
        required: false
        default: absent
        version_added: "2.0"
    update_cache:
        description:
            - update the package db first
        required: false
        default: "no"
        choices: [ "yes", "no" ]
notes:  []
requirements:
    - opkg
    - python
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
from ansible.module_utils.basic import *
__metaclass__ = type


STATES = ["present", "installed", "absent", "removed"]

FORCE = [
    "",
    "depends",
    "maintainer",
    "reinstall",
    "overwrite",
    "downgrade",
    "space",
    "postinstall",
    "remove",
    "checksum",
    "removal-of-dependent-packages"
]


def get_opkg_path(module):
    return module.get_bin_path('opkg', True, ['/bin'])


def update_package_db(module):
    """ Updates packages list. """
    rc, out, err = module.run_command("%s update" % get_opkg_path(module))
    if rc != 0:
        module.fail_json(msg="could not update package db")


def is_installed(module, package, state="present"):
    """ Returns whether a package is installed or not. """
    present = False
    if state != "present":
        return present
    command = get_opkg_path(module)
    rc, _, _ = module.run_command("%s list-installed | grep -q \"^%s \"" % (
        pipes.quote(command),
        pipes.quote(package)),
        use_unsafe_shell=True
    )
    if rc == 0:
        present = True
    return present


def query_package(module, package, state="present"):
    """
    Just a deprecated function who wrappe is_installed
    deprecated for bad namming semantic
    """
    return is_installed(module, package, state)


def opkg(module, package, force, action='install'):
    return module.run_command("{opkg} {action} {force} {package}".format(
        opkg=get_opkg_path(module),
        action=action,
        force=force,
        package=package)
    )


def remove_packages(module, packages):
    """ Uninstalls one or more packages if installed. """
    msg = "package(s) already absent"
    changed = False
    p = module.params
    force = p["force"]
    if force:
        force = "--force-%s" % force

    removed = []
    for package in packages:
        if not is_installed(module, package):
            continue
        rc, out, err = opkg(module=module, action='remove', package=package, force=force)
        if not is_installed(module, package):
            removed.append(package)
            continue
        module.fail_json(msg="failed to remove %s: %s" % (package, out))

    if removed:
        changed = True
        msg = "removed {} package(s)\n{}".format(len(removed), ",".join(removed))
    module.exit_json(changed=changed, msg=msg)


def install_packages(module, packages):
    """ Installs one or more packages if not already installed. """
    changed = False
    msg = "package(s) already present"
    p = module.params
    force = p["force"]
    if force:
        force = "--force-%s" % force

    installed = []
    for package in packages:
        if is_installed(module, package):
            continue
        rc, out, err = opkg(module=module, action='install', package=package, force=force)
        if is_installed(module, package):
            installed.append(package)
            continue
        module.fail_json(msg="failed to install %s: %s" % (package, out))

    if installed:
        changed = True
        msg = "installed {} package(s)\n{}".format(len(installed), ",".join(installed))
    module.exit_json(changed=changed, msg=msg)


def handle_package(state, module, pkgs):
    available_state = {
        "present": install_packages,
        "installed": install_packages,
        "absent": remove_packages,
        "removed": remove_packages,
    }
    available_state[state](module, get_opkg_path(module), pkgs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=["pkg"], required=True),
            state=dict(default="present", choices=STATES),
            force=dict(default="", choices=FORCE),
            update_cache=dict(default="no", aliases=["update-cache"], type='bool')
        )
    )
    p = module.params
    pkgs = p["name"].split(",")

    if p["update_cache"]:
        update_package_db(module, get_opkg_path(module))
    handle_package(p["state"], module,  pkgs)


if __name__ == '__main__':
    main()
