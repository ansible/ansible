from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.modules.cloud.vmware_httpapi.conftest import enable_vcr
from units.compat.mock import ANY


@enable_vcr()
def test_no_parameter(run_module):
    exit_json = run_module('vmware_appliance_access_info', {})
    exit_json.assert_called_with(
        ANY,
        consolecli={'value': True},
        dcui={'value': True},
        invocation={
            'module_args': {
                'allow_multiples': False,
                'log_level': 'normal',
                'status_code': [200],
                'access_mode': None},
            'module_kwargs': {
                'is_multipart': True,
                'use_object_handler': True}},
        shell={
            'value': {
                'enabled': False,
                'timeout': 0}},
        ssh={'value': True})
