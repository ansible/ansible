#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: r4e_rpm_ostree
version_added: 2.14.0
short_description: Ensure packages exist in a RHEL for Edge rpm-ostree based system
description:
  - Compatibility layer for using the "package" module for RHEL for Edge systems utilizing the RHEL System Roles.
author:
  - Adam Miller (@maxamillion)
requirements:
  - rpm-ostree
options:
  name:
    description:
      - A package name or package specifier with version, like C(name-1.0).
      - Comparison operators for package version are valid here C(>), C(<), C(>=), C(<=). Example - C(name>=1.0)
      - If a previous version is specified, the task also needs to turn C(allow_downgrade) on.
        See the C(allow_downgrade) documentation for caveats with downgrading packages.
      - When using state=latest, this can be C('*') which means run C(yum -y update).
      - You can also pass a url or a local path to a rpm file (using state=present).
        To operate on several packages this can accept a comma separated string of packages or (as of 2.0) a list of packages.
    aliases: [ pkg ]
    type: list
    elements: str
  state:
    description:
      - Whether to install (C(present) or C(installed), C(latest)), or remove (C(absent) or C(removed)) a package.
      - C(present) and C(installed) will simply ensure that a desired package is installed.
      - C(latest) will update the specified package if it's not of the latest available version.
      - C(absent) and C(removed) will remove the specified package.
      - Default is C(None), however in effect the default action is C(present) unless the C(autoremove) option is
        enabled for this module, then C(absent) is inferred.
    type: str
    choices: [ absent, installed, latest, present, removed ]
notes:
  - This module does not support installing or removing packages to/from an overlay as this is not supported
    by RHEL for Edge, packages needed should be defined in the osbuild Blueprint and provided to Image Builder
    at build time. This module exists only for C(package) module compatibility.
'''

EXAMPLES = '''
- name: Install htop and ansible on rpm-ostree based overlay
  ansible.builtin.rpm_ostree:
    name:
      - htop
      - ansible
    state: present
'''

RETURN = """
msg:
    description: status of rpm transaction
    returned: always
    type: str
    sample: "No changes made."
"""

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


def locally_installed(module, pkgname):
    (rc, out, err) = module.run_command('rpm -q {0}'.format(pkgname).split())
    return (rc == 0)


def rpm_ostree_transaction(module):
    pkgs = []

    if module.params['state'] in ['present', 'installed', 'latest']:
        for pkg in module.params['name']:
            if not locally_installed(module, pkg):
                pkgs.append(pkg)
    elif module.params['state'] in ['absent', 'removed']:
        for pkg in module.params['name']:
            if locally_installed(module, pkg):
                pkgs.append(pkg)

    if not pkgs:
        module.exit_json(msg="No changes made.")
    else:
        if module.params['state'] in ['present', 'installed', 'latest']:
            module.fail_json(msg="The following packages are absent in the currently booted rpm-ostree commit: %s" ' '.join(pkgs))
        else:
            module.fail_json(msg="The following packages are present in the currently booted rpm-ostree commit: %s" ' '.join(pkgs))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='list', elements='str', aliases=['pkg'], default=[]),
            state=dict(type='str', default=None, choices=['absent', 'installed', 'latest', 'present', 'removed']),
        ),
    )

    # Verify that the platform is an rpm-ostree based system
    if not os.path.exists("/run/ostree-booted"):
        module.fail_json(msg="Module rpm_ostree is only applicable for rpm-ostree based systems.")

    try:
        rpm_ostree_transaction(module)
    except Exception as e:
        module.fail_json(msg=to_text(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
