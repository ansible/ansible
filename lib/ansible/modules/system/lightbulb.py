#!/usr/bin/python
# Hello World example module by David Igou July 2017

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview', 'deprecated']
}

DOCUMENTATION = '''
---
module: lightbulb
description: This module does nothing then exits with msg="HELLO WORLD"
'''


EXAMPLES = '''
- name: lightbulb module
  lightbulb:
'''

RETURN = '''
msg:
   description: simple Hello World message
'''


from ansible.module_utils.basic import *

def main():
	module = AnsibleModule( argument_spec=dict(	))
	module.exit_json(changed=False, msg="HELLO WORLD")


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
	main()
