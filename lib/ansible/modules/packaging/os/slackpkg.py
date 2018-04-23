#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Kim Nørgaard
# Written by Kim Nørgaard <jasen@jasen.dk>
# Based on pkgng module written by bleader <bleader@ratonland.org>
# that was based on pkgin module written by Shaun Zinck <shaun.zinck at gmail.com>
# that was based on pacman module written by Afterburn <https://github.com/afterburn>
# that was based on apt module written by Matthew Williams <matthew@flowroute.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: slackpkg
short_description: Package manager for Slackware >= 12.2
description:
    - Manage binary packages for Slackware using 'slackpkg' which
      is available in versions after 12.2.
version_added: "2.0"
options:
    name:
        description:
            - name of package to install/remove
        required: true

    state:
        description:
            - state of the package, you can use "installed" as an alias for C(present) and removed as one for C(absent).
        choices: [ 'present', 'absent', 'latest' ]
        required: false
        default: present

    update_cache:
        description:
            - update the package database first
        required: false
        default: false
        type: bool

author: Kim Nørgaard (@KimNorgaard)
requirements: [ "Slackware >= 12.2" ]
'''

EXAMPLES = '''
# Install package foo
- slackpkg:
    name: foo
    state: present

# Remove packages foo and bar
- slackpkg:
    name: foo,bar
    state: absent

# Make sure that it is the most updated package
- slackpkg:
    name: foo
    state: latest
'''

from ansible.module_utils.basic import AnsibleModule


def query_package(module, slackpkg_path, name):

    import glob
    import platform

    machine = platform.machine()
    packages = glob.glob("/var/log/packages/%s-*-[%s|noarch]*" % (name,
                                                                  machine))

    if len(packages) > 0:
        return True

    return False


def remove_packages(module, slackpkg_path, packages):

    remove_c = 0
    # Using a for loop in case of error, we can report the package that failed
    for package in packages:
        # Query the package first, to see if we even need to remove
        if not query_package(module, slackpkg_path, package):
            continue

        if not module.check_mode:
            rc, out, err = module.run_command("%s -default_answer=y -batch=on \
                                              remove %s" % (slackpkg_path,
                                                            package))

        if not module.check_mode and query_package(module, slackpkg_path,
                                                   package):
            module.fail_json(msg="failed to remove %s: %s" % (package, out))

        remove_c += 1

    if remove_c > 0:

        module.exit_json(changed=True, msg="removed %s package(s)" % remove_c)

    module.exit_json(changed=False, msg="package(s) already absent")


def install_packages(module, slackpkg_path, packages):

    install_c = 0

    for package in packages:
        if query_package(module, slackpkg_path, package):
            continue

        if not module.check_mode:
            rc, out, err = module.run_command("%s -default_answer=y -batch=on \
                                              install %s" % (slackpkg_path,
                                                             package))

        if not module.check_mode and not query_package(module, slackpkg_path,
                                                       package):
            module.fail_json(msg="failed to install %s: %s" % (package, out),
                             stderr=err)

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="present %s package(s)"
                         % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def upgrade_packages(module, slackpkg_path, packages):
    install_c = 0

    for package in packages:
        if not module.check_mode:
            rc, out, err = module.run_command("%s -default_answer=y -batch=on \
                                              upgrade %s" % (slackpkg_path,
                                                             package))

        if not module.check_mode and not query_package(module, slackpkg_path,
                                                       package):
            module.fail_json(msg="failed to install %s: %s" % (package, out),
                             stderr=err)

        install_c += 1

    if install_c > 0:
        module.exit_json(changed=True, msg="present %s package(s)"
                         % (install_c))

    module.exit_json(changed=False, msg="package(s) already present")


def update_cache(module, slackpkg_path):
    rc, out, err = module.run_command("%s -batch=on update" % (slackpkg_path))
    if rc != 0:
        module.fail_json(msg="Could not update package cache")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="installed", choices=['installed', 'removed', 'absent', 'present', 'latest']),
            name=dict(aliases=["pkg"], required=True, type='list'),
            update_cache=dict(default=False, aliases=["update-cache"],
                              type='bool'),
        ),
        supports_check_mode=True)

    slackpkg_path = module.get_bin_path('slackpkg', True)

    p = module.params

    pkgs = p['name']

    if p["update_cache"]:
        update_cache(module, slackpkg_path)

    if p['state'] == 'latest':
        upgrade_packages(module, slackpkg_path, pkgs)

    elif p['state'] in ['present', 'installed']:
        install_packages(module, slackpkg_path, pkgs)

    elif p["state"] in ['removed', 'absent']:
        remove_packages(module, slackpkg_path, pkgs)


if __name__ == '__main__':
    main()
