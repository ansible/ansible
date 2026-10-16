#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
---
module: test_docs_short_description_in_return
description:
    - Test module without a short_description, but with a return value of that name
author:
    - Ansible Core Team
"""

EXAMPLES = """
"""

RETURN = """
short_description:
    description: A return value sharing its name with the top-level documentation key
    returned: always
    type: str
"""


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json(short_description='')


if __name__ == '__main__':
    main()
