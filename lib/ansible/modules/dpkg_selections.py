#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: dpkg_selections
short_description: Dpkg package selection selections
description:
    - Change dpkg package selection state via --get-selections and --set-selections.
version_added: "2.0"
author:
- Brian Brazil (@brian-brazil)  <brian.brazil@boxever.com>
options:
    name:
        description:
            - Name of the package.
        required: true
        type: str
    selection:
        description:
            - The selection state to set the package to.
        choices: [ 'install', 'hold', 'deinstall', 'purge' ]
        required: true
        type: str
notes:
    - This module won't cause any packages to be installed/removed/purged, use the C(apt) module for that.
'''
EXAMPLES = '''
- name: Prevent python from being upgraded
  dpkg_selections:
    name: python
    selection: hold
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            selection=dict(choices=['install', 'hold', 'deinstall', 'purge'], required=True)
        ),
        supports_check_mode=True,
    )

    dpkg = module.get_bin_path('dpkg', True)

    name = module.params['name']
    selection = module.params['selection']

    # Get current settings.
    rc, out, err = module.run_command([dpkg, '--get-selections', name], check_rc=True)
    if not out:
        current = 'not present'
    else:
        current = out.split()[1]

    changed = current != selection

    if module.check_mode or not changed:
        module.exit_json(changed=changed, before=current, after=selection)

    module.run_command([dpkg, '--set-selections'], data="%s %s" % (name, selection), check_rc=True)
    module.exit_json(changed=changed, before=current, after=selection)


if __name__ == '__main__':
    main()
