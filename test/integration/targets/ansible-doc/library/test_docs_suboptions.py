#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = """
---
module: test_docs_suboptions
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
options:
    with_suboptions:
        description:
            - An option with suboptions.
            - Use with care.
        type: dict
        suboptions:
            z_last:
                description: The last suboption.
                type: str
            m_middle:
                description:
                    - The suboption in the middle.
                    - Has its own suboptions.
                suboptions:
                    a_suboption:
                        description: A sub-suboption.
                        type: str
            a_first:
                description: The first suboption.
                type: str
"""

EXAMPLES = """
"""

RETURN = """
"""


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            test_docs_suboptions=dict(
                type='dict',
                options=dict(
                    a_first=dict(type='str'),
                    m_middle=dict(
                        type='dict',
                        options=dict(
                            a_suboption=dict(type='str')
                        ),
                    ),
                    z_last=dict(type='str'),
                ),
            ),
        ),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
