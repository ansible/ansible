#!/usr/bin/python

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
# overridden
from ansible.module_utils.ansible_release import data

results = {"data": data}

arg_spec = dict(
    foo=dict(type='str', aliases=['baz'], deprecated_aliases=[dict(name='baz', version='9.99')])
)

AnsibleModule(argument_spec=arg_spec).exit_json(**results)
