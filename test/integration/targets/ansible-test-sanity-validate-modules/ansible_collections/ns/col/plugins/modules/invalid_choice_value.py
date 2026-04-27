#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
module: invalid_choice_value
short_description: Test for equal length of choices with correct options
description: Test for equal length of choices with correct options
author:
  - Ansible Core Team
options:
  caching:
    description:
      - Type of Caching.
    type: str
    choices:
      - ReadOnly
      - ReadWrite
"""

EXAMPLES = """#"""
RETURN = """"""

from ansible.module_utils.basic import AnsibleModule


if __name__ == "__main__":
    module = AnsibleModule(
        argument_spec=dict(caching=dict(type="str", choices=["ReadOnly", "ReadOnly"])),
        supports_check_mode=False,
    )
    module.exit_json()
