#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: no_callable
short_description: No callale test module
description: No callable test module.
author:
  - Ansible Core Team
'''

EXAMPLES = '''#'''
RETURN = ''''''

from ansible.module_utils.basic import AnsibleModule


if __name__ == '__main__':
    module = AnsibleModule(argument_spec=dict())
    module.exit_json()
