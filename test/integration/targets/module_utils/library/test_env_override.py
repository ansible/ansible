#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.json_utils import data
from ansible.module_utils.mork import data as mork_data

results = {"json_utils": data, "mork": mork_data}

AnsibleModule(argument_spec=dict()).exit_json(**results)
