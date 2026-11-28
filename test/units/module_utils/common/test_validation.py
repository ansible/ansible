from __future__ import annotations

import pytest

from ansible.module_utils.common.validation import check_missing_parameters


@pytest.mark.parametrize('value', [0, False, '', [], {}, ()])
def test_check_missing_parameters_accepts_present_falsy_values(value):
    assert check_missing_parameters({'name': value}, ['name']) == []


@pytest.mark.parametrize('parameters', [{}, {'name': None}])
def test_check_missing_parameters_reports_absent_values(parameters):
    with pytest.raises(TypeError, match='missing required arguments: name'):
        check_missing_parameters(parameters, ['name'])
