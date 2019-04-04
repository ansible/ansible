#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule

module = AnsibleModule(argument_spec=dict())

module.exit_json(**{'tempdir': module._remote_tmp})
