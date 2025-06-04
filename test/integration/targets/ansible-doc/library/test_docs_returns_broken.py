#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
---
module: test_docs_returns_broken
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
"""

EXAMPLES = """
"""

RETURN = """
test:
    description: A test return value.
   type: str

broken_key: [
"""


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
