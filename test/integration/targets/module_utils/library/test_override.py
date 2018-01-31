#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts import data

results = {"data": data}

AnsibleModule(argument_spec=dict()).exit_json(**results)
