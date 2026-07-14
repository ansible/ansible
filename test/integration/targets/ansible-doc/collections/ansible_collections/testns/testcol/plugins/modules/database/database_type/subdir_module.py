#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
---
module: subdir_module
short_description: A module in multiple subdirectories
description:
    - A module in multiple subdirectories
author:
    - Ansible Core Team
version_added: 1.0.0
options: {}
"""

EXAMPLES = """
"""

RETURN = """
"""


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
