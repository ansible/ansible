#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
---
module: test_docs_invalid_short_description
short_description:
    not: a string
description:
    - Test module
author:
    - Ansible Core Team
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
