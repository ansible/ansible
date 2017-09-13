#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Kairo Araujo
# Written by Kairo Araujo <kairo@kairo.eti.br>
#
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: installp
short_description: Installing packages for AIX
description:
    - Manage packages for AIX using 'installp'.
version_added: "2.5"
options:
    name:
        description:
            - Name of package to install/remove. To operate on several packages
              this can accept a comma separated.
        required: true
    repository_path:
        description:
            - Path with AIX packages (required to install).
        required: no
    state:
        description:
            - State of the package.
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    accept_license:
        description:
            - Accept license for package.
        choices: [ 'yes', 'no' ]
        required: false
        default: no
    package_action:
        description:
            - Action for package.
        choices: [ 'preview', 'install' ]
        required: false
        default: preview

author: "Kairo Araujo (@kairoaraujo)"
'''

EXAMPLES = '''
# Install package foo
- installp:
    name: foo
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

# Install bos.sysmgt that includes bos.sysmgt.nim.master, bos.sysmgt.nim.spot
# and bos.sysmgt.trcgui_samp
- installp:
    name: bos.sysmgt
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

# Install bos.sysmgt.nim.master only
- installp:
    name: bos.sysmgt.nim.master
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

# Install bos.sysmgt.nim.master and bos.sysmgt.nim.spot
- installp:
    name: bos.sysmgt.nim.master, bos.sysmgt.nim.spot
    repository_path: /repository/AIX71/installp/base
    package_license: yes
    state: present

# Remove packages foo and bar
- installp:
    name: foo,bar
    state: absent
'''

RETURN = '''
changed:
    description: Return changed for installp actions as true or false.
    returned: always
    type: boolean
    version_added: 2.5
'''

from ansible.module_utils.basic import AnsibleModule

package_actions_param = {
    'preview': '-p',
    'install': '',
}

accept_license_param = {
    True: '-Y',
    'no': '',
}


def remove(module, installp_cmd, packages, package_action):
    remove_count = 0

    for package in packages:

        rc, remove_out, err = module.run_command('%s -u %s %s' % (
            installp_cmd,
            package,
            package_actions_param[package_action]))
        if rc != 0:
            module.fail_json(msg="Failed to uninstall the package %s" %
                                 package, rc=rc, err=err)

        else:
            remove_count += 1

    if remove_count > 0:
        module.exit_json(changed=True, msg="%s packages removed" %
                                           remove_count)
    else:
        module.exit_json(changed=False, msg="No packages removed")


def install(module, installp_cmd, packages, repository_path, package_action,
            accept_license):
    install_count = 0

    for package in packages:

        rc, install_out, err = module.run_command('%s -a %s -X %s -d %s %s'
                                                  % (installp_cmd,
                                                     package_actions_param[
                                                         package_action],
                                                     accept_license_param[
                                                         accept_license],
                                                     repository_path,
                                                     package
                                                     ))
        if rc != 0:
            module.fail_json(msg="Failed to install the package %s" % package,
                             rc=rc, err=err)
        else:
            install_count += 1

    if install_count > 0:
        module.exit_json(changed=True, msg="%s packages installed" %
                                           install_count)
    else:
        module.exit_json(changed=False, msg="No packages installed")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=["pkg"], required=True),
            repository_path=dict(type='str', default=None),
            accept_license=dict(type='bool', default='no'),
            state=dict(default="present", choices=["present", "absent"]),
            package_action=dict(default="preview",
                                choices=["preview", "install"]),
        ))

    installp_params = module.params
    pkgs = installp_params["name"].split(",")

    installp_cmd = module.get_bin_path('installp', True)

    if installp_params["state"] == "present":
        if installp_params["repository_path"] is None:
            module.fail_json(msg="repository_path is required to install "
                                 "package")

        install(module, installp_cmd, pkgs, installp_params["repository_path"],
                installp_params["package_action"], installp_params["accept_license"])

    elif installp_params["state"] == "absent":
        remove(module, installp_cmd, pkgs, installp_params["package_action"])


if __name__ == '__main__':
    main()
