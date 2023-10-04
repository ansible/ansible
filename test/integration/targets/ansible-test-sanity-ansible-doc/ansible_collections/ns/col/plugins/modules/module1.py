#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
module: module1
short_description: Hello test module
description: Hello test module.
options: {}
author:
  - Ansible Core Team
'''

EXAMPLES = '''
- minimal:
'''

RETURN = ''''''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={},
    )

    module.exit_json()


if __name__ == '__main__':
    main()
