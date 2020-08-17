#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: test_docs_returns
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
options:
    test:
        type: str
'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            test=dict(type='str'),
        ),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
