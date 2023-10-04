#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = '''
---
module: metadata
version_added: 2.12
short_description: Test module with a specific name
description: Test module with a specific name
options:
  data:
    description: Required option to test module_defaults work
    required: True
    type: str
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
        argument_spec=dict(
            data=dict(type='str', required=True),
        ),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
