# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils import basic
from ansible.module_utils.basic import AnsibleModule, jsonify

DATA = (
    ('_check_type_str', 'sample_value', 'sample_value'),
    ('_check_type_str', 1, '1'),
    ('_check_type_list', ['1'], ['1']),
    ('_check_type_list', '1,2,3', ['1', '2', '3']),
    ('_check_type_list', 1, ['1']),
    ('_check_type_dict', {'sample_key': 'sample_value'}, {'sample_key': 'sample_value'}),
    ('_check_type_dict', '{"sample_key": "sample_value"}', {'sample_key': 'sample_value'}),
    ('_check_type_dict', '"sample_key"="sample_value"', {'sample_key': 'sample_value'}),
    ('_check_type_bool', True, True),
    ('_check_type_bool', False, False),
    ('_check_type_int', 1, 1),
    ('_check_type_int', '1', 1),
    ('_check_type_float', '1.0', 1.0),
    ('_check_type_float', b'1.0', 1.0),
    ('_check_type_float', "1.0", 1.0),
    ('_check_type_float', """1.0""", 1.0),
    ('_check_type_float', 1.0, 1.0),
    ('_check_type_path', '/home', '/home'),
    ('_check_type_jsonarg', 'sample_str', 'sample_str'),
    ('_check_type_jsonarg', "sample_str", 'sample_str'),
    ('_check_type_jsonarg', """sample_str""", 'sample_str'),
    ('_check_type_jsonarg', b"sample_str", b"sample_str"),
    ('_check_type_raw', "42", "42"),
)


@pytest.mark.parametrize('func, test_value, expected', DATA)
def test_check_type_positive(mocker, func, test_value, expected):
    mock_type_check = mocker.MagicMock()
    test_func = getattr(AnsibleModule, func)
    if func == '_check_type_path':
        mocker.patch.object(mock_type_check, '_check_type_str', return_value=expected)
    assert test_func(mock_type_check, 'sample', test_value) == expected


def test_check_type_str_err_negative(mocker):
    mock_type_check = mocker.MagicMock()
    mock_type_check._string_conversion_action = 'error'
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_str(mock_type_check, 'sample', [])
    assert "Quote the entire value to ensure it does not change" in str(exc.value)


def test_check_type_list_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_list(mock_type_check, 'sample', {})
    assert "cannot be converted to a list" in str(exc.value)


def test_check_type_dict_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_dict(mock_type_check, 'sample', '1')
    assert "dictionary requested, could not parse JSON or key=value" in str(exc.value)


def test_check_type_dict_to_int_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_dict(mock_type_check, 'sample', 1)
    assert "cannot be converted to a dict" in str(exc.value)


def test_check_type_bool_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_bool(mock_type_check, 'sample', [])
    assert "cannot be converted to a bool" in str(exc.value)


def test_check_type_int_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_int(mock_type_check, 'sample', 'aaa')
    assert "cannot be converted to an int" in str(exc.value)


def test_check_type_float_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_float(mock_type_check, 'sample', 'aaa')
    assert "cannot be converted to a float" in str(exc.value)


def test_check_type_jsonarg_negative(mocker):
    mock_type_check = mocker.MagicMock()
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_jsonarg(mock_type_check, 'sample', True)
    assert "cannot be converted to a json string" in str(exc.value)


def test_check_type_bytes_negative(mocker):
    mock_type_check = mocker.MagicMock()
    mock_type_check.human_to_bytes.side_effect = ValueError("interpret following string")
    with pytest.raises(TypeError) as exc:
        AnsibleModule._check_type_bytes(mock_type_check, 'sample', True)
    assert "cannot be converted to a Byte value" in str(exc.value)
