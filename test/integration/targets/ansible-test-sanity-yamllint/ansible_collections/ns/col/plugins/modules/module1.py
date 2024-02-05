#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: module1
short_description: Hello test module
description: Hello test module.
options: {}
author:
  - Ansible Core Team
short_description: Duplicate short description
"""

EXAMPLES = r"""
- minimal:
"""

RETURN = r"""
invalid_yaml:
    bad_indent:
  usual_indent:
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={},
    )

    module.exit_json()


if __name__ == "__main__":
    main()
