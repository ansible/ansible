# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: dpkg_selections
short_description: Dpkg package selection selections
description:
    - Change dpkg package selection state via C(--get-selections) and C(--set-selections).
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
extends_documentation_fragment:
- action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        support: full
        platforms: debian
notes:
    - This module will not cause any packages to be installed/removed/purged, use the M(ansible.builtin.apt) module for that.
"""
EXAMPLES = """
- name: Prevent python from being upgraded
  ansible.builtin.dpkg_selections:
    name: python
    selection: hold

- name: Allow python to be upgraded
  ansible.builtin.dpkg_selections:
    name: python
    selection: install
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            selection=dict(choices=['install', 'hold', 'deinstall', 'purge'], required=True)
        ),
        supports_check_mode=True,
    )

    dpkg = module.get_bin_path('dpkg', True)

    locale = get_best_parsable_locale(module)
    DPKG_ENV = dict(LANG=locale, LC_ALL=locale, LC_MESSAGES=locale, LC_CTYPE=locale, LANGUAGE=locale)
    module.run_command_environ_update = DPKG_ENV

    name = module.params['name']
    selection = module.params['selection']

    # Get current settings.
    rc, out, err = module.run_command([dpkg, '--get-selections', name], check_rc=True)
    if 'no packages found matching' in err:
        module.fail_json(msg="Failed to find package '%s' to perform selection '%s'." % (name, selection))
    elif not out:
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
