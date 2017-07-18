#!/usr/bin/python
import httplib
import urllib
 
def main():
	module = AnsibleModule(
		argument_spec = dict(		)
	)
	module.exit_json(changed=True, msg="hello world")

from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()