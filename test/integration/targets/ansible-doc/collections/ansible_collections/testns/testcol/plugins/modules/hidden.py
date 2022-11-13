#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hidden
short_description: A hidden module
description:
    - This is private.
author:
    - Ansible Core Team
version_added: 1.2.0
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

    module.exit_json(msg='This is private!')


if __name__ == '__main__':
    main()
