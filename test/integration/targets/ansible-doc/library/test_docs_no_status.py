#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: test_docs_no_status
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
