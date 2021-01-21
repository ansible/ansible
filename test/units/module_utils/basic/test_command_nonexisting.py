from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest
import json
import sys
import pytest
import subprocess
import ansible.module_utils.basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic


def test_run_non_existent_command(monkeypatch):
    """ Test that `command` returns std{out,err} even if the executable is not found """
    def fail_json(msg, **kwargs):
        assert kwargs["stderr"] == b''
        assert kwargs["stdout"] == b''
        sys.exit(1)

    def popen(*args, **kwargs):
        raise OSError()

    monkeypatch.setattr(basic, '_ANSIBLE_ARGS', to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': {}})))
    monkeypatch.setattr(subprocess, 'Popen', popen)

    am = basic.AnsibleModule(argument_spec={})
    monkeypatch.setattr(am, 'fail_json', fail_json)
    with pytest.raises(SystemExit):
        am.run_command("lecho", "whatever")
