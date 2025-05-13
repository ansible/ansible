#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
module: import_order
short_description: Import order test module
description: Import order test module.
author:
  - Ansible Core Team
"""

EXAMPLES = """#"""
RETURN = """"""


if __name__ == '__main__':
    module = AnsibleModule(argument_spec=dict())
    module.exit_json()
