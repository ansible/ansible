from __future__ import annotations

from ansible.module_utils.basic import _load_params, AnsibleModule
from ansible.module_utils.testing import patch_module_args


def do_echo():
    p = _load_params()

    with patch_module_args():
        module = AnsibleModule(argument_spec={})
        module.exit_json(args_in=p)
