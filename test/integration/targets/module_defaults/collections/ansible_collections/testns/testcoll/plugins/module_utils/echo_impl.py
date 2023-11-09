from __future__ import annotations

import json
from ansible.module_utils import basic
from ansible.module_utils.basic import _load_params, AnsibleModule


def do_echo():
    p = _load_params()
    d = json.loads(basic._ANSIBLE_ARGS)
    d['ANSIBLE_MODULE_ARGS'] = {}
    basic._ANSIBLE_ARGS = json.dumps(d).encode('utf-8')
    module = AnsibleModule(argument_spec={})
    module.exit_json(args_in=p)
