#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
module: wrong_aliases
short_description: Aliases that are attached to the wrong option in documentation
description: Aliases that are attached to the wrong option in documentation.
author:
  - Ansible Core Team
options:
  foo:
    description: Foo.
    type: str
    aliases:
      - bam
  bar:
    description: Bar.
    type: str
'''

EXAMPLES = '''#'''
RETURN = ''''''

from ansible.module_utils.basic import AnsibleModule


def main():
    AnsibleModule(
        argument_spec=dict(
            foo=dict(
                type='str',
            ),
            bar=dict(
                type='str',
                aliases=[
                    'bam'
                ],
            ),
        ),
    )


if __name__ == '__main__':
    main()
