#!/usr/bin/python

from ansible.module_utils.basic import *

def main():
	module = AnsibleModule( argument_spec=dict(	))
	module.exit_json(changed=False, msg="HELLO WORLD")


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
	main()
