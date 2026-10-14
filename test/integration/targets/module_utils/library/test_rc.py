#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

module = AnsibleModule(dict(failed=dict(type='bool')))

result = {'rc': 1}

if module.params["failed"] is not None:
    result['failed'] = module.params["failed"]

module.exit_json(**result)
