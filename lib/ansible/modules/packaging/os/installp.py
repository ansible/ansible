#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Kairo Araujo <kairo@kairo.eti.br>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: installp
author:
- Kairo Araujo (@kairoaraujo)
short_description: Manage packages on AIX
description:
  - Manage packages using 'installp' on AIX
version_added: '2.8'
options:
  accept_license:
    description:
    - Whether to accept the license for the package(s).
    type: bool
    default: no
  name:
    description:
    - One or more packages to install or remove.
    - Use C(all) to install all packages available on informed C(repository_path).
    type: list
    required: true
    aliases: [ pkg ]
  repository_path:
    description:
    - Path with AIX packages (required to install).
    type: path
  state:
    description:
    - Whether the package needs to be present on or absent from the system.
    type: str
    choices: [ absent, present ]
    default: present
notes:
- If the package is already installed, even the package/fileset is new, the module will not install it.
'''

EXAMPLES = r'''
- name: Install package foo
  installp:
    name: foo
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

- name: Install bos.sysmgt that includes bos.sysmgt.nim.master, bos.sysmgt.nim.spot
  installp:
    name: bos.sysmgt
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

- name: Install bos.sysmgt.nim.master only
  installp:
    name: bos.sysmgt.nim.master
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

- name: Install bos.sysmgt.nim.master and bos.sysmgt.nim.spot
  installp:
    name: bos.sysmgt.nim.master, bos.sysmgt.nim.spot
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

- name: Remove packages bos.sysmgt.nim.master
  installp:
    name: bos.sysmgt.nim.master
    state: absent
'''

RETURN = r''' # '''

import os
import re

from ansible.module_utils.basic import AnsibleModule


def _check_new_pkg(module, package, repository_path):
    """
    Check if the package of fileset is correct name and repository path.

    :param module: Ansible module arguments spec.
    :param package: Package/fileset name.
    :param repository_path: Repository package path.
    :return: Bool, package information.
    """

    if os.path.isdir(repository_path):
        installp_cmd = module.get_bin_path('installp', True)
        rc, package_result, err = module.run_command("%s -l -MR -d %s" % (installp_cmd, repository_path))
        if rc != 0:
            module.fail_json(msg="Failed to run installp.", rc=rc, err=err)

        if package == 'all':
            pkg_info = "All packages on dir"
            return True, pkg_info

        else:
            pkg_info = {}
            for line in package_result.splitlines():
                if re.findall(package, line):
                    pkg_name = line.split()[0].strip()
                    pkg_version = line.split()[1].strip()
                    pkg_info[pkg_name] = pkg_version

                    return True, pkg_info

        return False, None

    else:
        module.fail_json(msg="Repository path %s is not valid." % repository_path)


def _check_installed_pkg(module, package, repository_path):
    """
    Check the package on AIX.
    It verifies if the package is installed and informations

    :param module: Ansible module parameters spec.
    :param package: Package/fileset name.
    :param repository_path: Repository package path.
    :return: Bool, package data.
    """

    lslpp_cmd = module.get_bin_path('lslpp', True)
    rc, lslpp_result, err = module.run_command("%s -lcq %s*" % (lslpp_cmd, package))

    if rc == 1:
        package_state = ' '.join(err.split()[-2:])
        if package_state == 'not installed.':
            return False, None
        else:
            module.fail_json(msg="Failed to run lslpp.", rc=rc, err=err)

    if rc != 0:
        module.fail_json(msg="Failed to run lslpp.", rc=rc, err=err)

    pkg_data = {}
    full_pkg_data = lslpp_result.splitlines()
    for line in full_pkg_data:
        pkg_name, fileset, level = line.split(':')[0:3]
        pkg_data[pkg_name] = fileset, level

    return True, pkg_data


def remove(module, installp_cmd, packages):
    repository_path = None
    remove_count = 0
    removed_pkgs = []
    not_found_pkg = []
    for package in packages:
        pkg_check, dummy = _check_installed_pkg(module, package, repository_path)

        if pkg_check:
            if not module.check_mode:
                rc, remove_out, err = module.run_command("%s -u %s" % (installp_cmd, package))
                if rc != 0:
                    module.fail_json(msg="Failed to run installp.", rc=rc, err=err)
            remove_count += 1
            removed_pkgs.append(package)

        else:
            not_found_pkg.append(package)

    if remove_count > 0:
        if len(not_found_pkg) > 1:
            not_found_pkg.insert(0, "Package(s) not found: ")

        changed = True
        msg = "Packages removed: %s. %s " % (' '.join(removed_pkgs), ' '.join(not_found_pkg))

    else:
        changed = False
        msg = ("No packages removed, all packages not found: %s" % ' '.join(not_found_pkg))

    return changed, msg


def install(module, installp_cmd, packages, repository_path, accept_license):
    installed_pkgs = []
    not_found_pkgs = []
    already_installed_pkgs = {}

    accept_license_param = {
        True: '-Y',
        False: '',
    }

    # Validate if package exists on repository path.
    for package in packages:
        pkg_check, pkg_data = _check_new_pkg(module, package, repository_path)

        # If package exists on repository path, check if package is installed.
        if pkg_check:
            pkg_check_current, pkg_info = _check_installed_pkg(module, package, repository_path)

            # If package is already installed.
            if pkg_check_current:
                # Check if package is a package and not a fileset, get version
                # and add the package into already installed list
                if package in pkg_info.keys():
                    already_installed_pkgs[package] = pkg_info[package][1]

                else:
                    # If the package is not a package but a fileset, confirm
                    # and add the fileset/package into already installed list
                    for key in pkg_info.keys():
                        if package in pkg_info[key]:
                            already_installed_pkgs[package] = pkg_info[key][1]

            else:
                if not module.check_mode:
                    rc, out, err = module.run_command("%s -a %s -X -d %s %s" % (installp_cmd, accept_license_param[accept_license], repository_path, package))
                    if rc != 0:
                        module.fail_json(msg="Failed to run installp", rc=rc, err=err)
                installed_pkgs.append(package)

        else:
            not_found_pkgs.append(package)

    if len(installed_pkgs) > 0:
        installed_msg = (" Installed: %s." % ' '.join(installed_pkgs))
    else:
        installed_msg = ''

    if len(not_found_pkgs) > 0:
        not_found_msg = (" Not found: %s." % ' '.join(not_found_pkgs))
    else:
        not_found_msg = ''

    if len(already_installed_pkgs) > 0:
        already_installed_msg = (" Already installed: %s." % already_installed_pkgs)
    else:
        already_installed_msg = ''

    if len(installed_pkgs) > 0:
        changed = True
        msg = ("%s%s%s" % (installed_msg, not_found_msg, already_installed_msg))
    else:
        changed = False
        msg = ("No packages installed.%s%s%s" % (installed_msg, not_found_msg, already_installed_msg))

    return changed, msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', required=True, aliases=['pkg']),
            repository_path=dict(type='path'),
            accept_license=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
    )

    name = module.params['name']
    repository_path = module.params['repository_path']
    accept_license = module.params['accept_license']
    state = module.params['state']

    installp_cmd = module.get_bin_path('installp', True)

    if state == 'present':
        if repository_path is None:
            module.fail_json(msg="repository_path is required to install package")

        changed, msg = install(module, installp_cmd, name, repository_path, accept_license)

    elif state == 'absent':
        changed, msg = remove(module, installp_cmd, name)

    else:
        module.fail_json(changed=False, msg="Unexpected state.")

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
