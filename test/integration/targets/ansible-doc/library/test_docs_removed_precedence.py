#!/usr/bin/python
from __future__ import annotations


DOCUMENTATION = '''
---
module: test_docs_removed_precedence
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
deprecated:
  alternative: new_module
  why: Updated module released with more functionality
  removed_at_date: '2022-06-01'
  removed_in: '2.14'
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
