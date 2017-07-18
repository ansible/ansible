#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: lightbulb
author: "Derek Foster (@fostimus)"
version_added: "2.3.1.0"
short_description: "Hello World"
requirements: 
description:
    - Prints "hello world to msg"
notes:
    - For Windows targets, use the M(win_group) module instead.
'''

EXAMPLES = '''
# Example group command from Ansible Playbooks
- lightbulb:
'''

import q
import pdb
import Cmd

def main():
	module = AnsibleModule(
		argument_spec = dict()
	)
	foo = "hello world"
	q(foo)
	pdb.set_trace()
	module.exit_json(changed=True, msg=foo)

from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()