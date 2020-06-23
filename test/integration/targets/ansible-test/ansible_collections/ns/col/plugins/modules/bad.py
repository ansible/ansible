#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: bad
short_description: Bad test module
description: Bad test module.
author:
  - Ansible Core Team
'''

EXAMPLES = '''
- bad:
'''

RETURN = ''''''

from ansible.module_utils.basic import AnsibleModule
from ansible import constants  # intentionally trigger pylint ansible-bad-module-import error


def main():
    module = AnsibleModule(
        argument_spec=dict(),
    )

    module.exit_json()


if __name__ == '__main__':
    main()
