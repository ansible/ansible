#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule

m = AnsibleModule(argument_spec=dict())
m.exit_json(changed=False, invocation=dict(manually_generated=True))
