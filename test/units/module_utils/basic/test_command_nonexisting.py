from __future__ import annotations

import sys
import pytest
import subprocess

from ansible.module_utils import basic
from ansible.module_utils.testing import patch_module_args


def test_run_non_existent_command(monkeypatch):
    """ Test that `command` returns std{out,err} even if the executable is not found """
    def fail_json(msg, **kwargs):
        assert kwargs["stderr"] == ''
        assert kwargs["stdout"] == ''
        sys.exit(1)

    def popen(*args, **kwargs):
        raise OSError()

    monkeypatch.setattr(subprocess, 'Popen', popen)

    with patch_module_args():
        am = basic.AnsibleModule(argument_spec={})

    monkeypatch.setattr(am, 'fail_json', fail_json)
    with pytest.raises(SystemExit):
        am.run_command("lecho", "whatever")
