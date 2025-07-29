#!/usr/bin/python

from __future__ import annotations


DOCUMENTATION = '''
---
module: test_docs_returns
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
'''

EXAMPLES = '''
'''

RETURN = '''
m_middle:
    description:
        - This should be in the middle.
        - Has some more data
    type: dict
    returned: success and 1st of month
    contains:
        suboption:
            description: A suboption.
            type: str
            choices: [ARF, BARN, c_without_capital_first_letter]

a_first:
    description: A first result.
    type: str
    returned: success

z_last:
    example: this is a merge
extends_documentation_fragment:
    - test_return_frag
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
