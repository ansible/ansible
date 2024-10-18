#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
module: file_common_args
short_description: using file common args
description: Using file common args.
author:
  - Ansible Core Team
options:
  name:
    description: The name
    type: str
"""

EXAMPLES = """#"""
RETURN = """"""

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str'),
        ),
        add_file_common_args=True,
    )
    module.exit_json()
