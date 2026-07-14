from __future__ import annotations

import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common import warnings

from ansible.module_utils.common.warnings import error_as_warning
from ansible.module_utils.testing import patch_module_args

pytestmark = pytest.mark.usefixtures("as_target", "module_env_mocker")


def test_error_as_warning() -> None:
    try:
        raise Exception('hello')
    except Exception as ex:
        error_as_warning('Warning message', ex)

    assert warnings.get_warning_messages() == ('Warning message: hello',)
    assert len(warnings.get_warnings()) == 1


def test_error_as_warning_via_module() -> None:
    with patch_module_args():
        am = AnsibleModule(argument_spec={})

    try:
        raise Exception('hello')
    except Exception as ex:
        am.error_as_warning('Warning message', ex)

    assert warnings.get_warning_messages() == ('Warning message: hello',)
    assert len(warnings.get_warnings()) == 1
