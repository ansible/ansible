import pytest

from conftest import enable_vcr
from units.compat.mock import ANY

@enable_vcr()
def test_no_parameter(run_module):
    exit_json, fail_json = run_module('vmware_cis_category_info', {})
    exit_json.assert_called_with(
        ANY,
        invocation={
            'module_args': {
                'allow_multiples': False,
                'log_level': 'normal',
                'status_code': [200],
                'category_name': None,
                'category_id': None,
                'used_by_name': None,
                'used_by_type': None,
                'used_by_id': None},
            'module_kwargs': {
                'is_multipart': False,
                'use_object_handler': False}})
