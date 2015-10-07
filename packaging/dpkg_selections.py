#!/usr/bin/python
# -*- coding: utf-8 -*-
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

DOCUMENTATION = '''
---
module: dpkg_selections
short_description: Dpkg package selection selections
description:
    - Change dpkg package selection state via --get-selections and --set-selections.
version_added: "2.0"
author: Brian Brazil <brian.brazil@boxever.com>
options:
    name:
        description:
            - Name of the package
        required: true
    selection:
        description:
            - The selection state to set the package to.
        choices: [ 'install', 'hold', 'deinstall', 'purge' ]
        required: true
notes:
    - This module won't cause any packages to be installed/removed/purged, use the C(apt) module for that.
'''
EXAMPLES = '''
# Prevent python from being upgraded.
- dpkg_selections: name=python selection=hold
'''

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            selection = dict(choices=['install', 'hold', 'deinstall', 'purge'])
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


from ansible.module_utils.basic import *
main()
