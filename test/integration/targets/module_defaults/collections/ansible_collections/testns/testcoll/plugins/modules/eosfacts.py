# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: eosfacts
short_description: module to test module_defaults
description: module to test module_defaults
version_added: '2.13'
"""

EXAMPLES = r"""
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            eosfacts=dict(type=bool),
        ),
        supports_check_mode=True
    )
    module.exit_json(eosfacts=module.params['eosfacts'])


if __name__ == '__main__':
    main()
