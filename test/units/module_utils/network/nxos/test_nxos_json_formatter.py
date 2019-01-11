# Copyright: (c) 2019, Olivier Blin <olivier.oblin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from ansible.module_utils.network.nxos.nxos_json_formatter import nxos_json_formatter, NxosJsonFormatterError


def test_dict_path_with_one_element():
    data = nxos_json_formatter({}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': []}}


def test_dict_path_with_invalid_struct():
    with pytest.raises(NxosJsonFormatterError, message="The last element must be a dict, got <type 'list'>"):
        nxos_json_formatter([], ['a'])


def test_empty_string_case():
    data = nxos_json_formatter("", ['a'])
    assert data == {'TABLE_a': {'ROW_a': []}}


def test_invalid_struct_to_build_nxos_element():
    with pytest.raises(NxosJsonFormatterError, message="The last element must be a dict, got <type 'str'>"):
        nxos_json_formatter({'TABLE_a': {'ROW_a': ""}}, ['TABLE_a.ROW_a.b'])


def test_dict_path_with_missing_key_after_convert():
    with pytest.raises(NxosJsonFormatterError, message="Missing key 'a'"):
        nxos_json_formatter({}, ['a', 'a.b'])


def test_long_dict_path():
    data = nxos_json_formatter({'a': {'b': {}}}, ['a.b.c'])
    assert data == {'a': {'b': {'TABLE_c': {'ROW_c': []}}}}


def test_dict_path_with_missing_key_before_convert():
    with pytest.raises(NxosJsonFormatterError, message="Missing key 'bad'"):
        nxos_json_formatter({'a': {'b': {}}}, ['a.bad.c'])


def test_long_dict_path_with_invalid_struct():
    with pytest.raises(NxosJsonFormatterError, message="Expected a dict with key 'b', got <type 'list'>"):
        nxos_json_formatter({'a': []}, ['a.b.c'])


def test_list_path_with_empty_list():
    data = nxos_json_formatter([], ['*.a'])
    assert data == []


def test_list_path_with_items():
    data = nxos_json_formatter([{}, {}], ['*.a'])
    assert data == [{'TABLE_a': {'ROW_a': []}}, {'TABLE_a': {'ROW_a': []}}]


def test_list_path_with_complex_items():
    data = nxos_json_formatter([{'a': {}}, {'a': {}}], ['*.a.b'])
    assert data == [{'a': {'TABLE_b': {'ROW_b': []}}}, {'a': {'TABLE_b': {'ROW_b': []}}}]


def test_double_list_path_with_items():
    data = nxos_json_formatter([[{}, {}]], ['*.*.a'])
    assert data == [[{'TABLE_a': {'ROW_a': []}}, {'TABLE_a': {'ROW_a': []}}]]


def test_list_path_with_invalid_struct():
    with pytest.raises(NxosJsonFormatterError, message="Expected a list (*), got <type 'dict'>"):
        nxos_json_formatter([{}], ['*.*'])


def test_rewrite_with_nothing_to_do():
    data = nxos_json_formatter({'TABLE_a': {'ROW_a': []}}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': []}}


def test_rewrite_with_one_item():
    data = nxos_json_formatter({'TABLE_a': {'ROW_a': {}}}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': [{}]}}


def test_rewrite_with_nothing_to_do_2():
    data = nxos_json_formatter({'TABLE_a': {'ROW_a': [{'c': 1, 'd': 2}, {'c': 5, 'd': 4}]}}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': [{'c': 1, 'd': 2}, {'c': 5, 'd': 4}]}}


def test_rewrite_with_one_item_2():
    data = nxos_json_formatter({'TABLE_a': {'ROW_a': {'c': 1, 'd': 2}}}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': [{'c': 1, 'd': 2}]}}


def test_alternative_format_alternative():
    data = nxos_json_formatter({'TABLE_a': [{'ROW_a': {'vrf': 1}}, {'ROW_a': {'vrf': 2}}]}, ['a'])
    assert data == {'TABLE_a': {'ROW_a': [{'vrf': 1}, {'vrf': 2}]}}


def test_alternative_format_with_invalid_TABLE():
    with pytest.raises(NxosJsonFormatterError, message="The last element (TABLE_a) must be a dict or a list, got <type 'int'>"):
        nxos_json_formatter({'TABLE_a': 5}, ['a'])


def test_alternative_format_with_invalid_ROW():
    with pytest.raises(NxosJsonFormatterError, message="The last element (ROW_a) must be a dict, got <type 'int'>"):
        nxos_json_formatter({'TABLE_a': [{'ROW_a': {'vrf': 1}}, {'ROW_a': 2}]}, ['a'])


def test_alternative_format_with_missing_ROW():
    with pytest.raises(NxosJsonFormatterError, message="The last element (ROW_a) is missing"):
        nxos_json_formatter({'TABLE_a': [{'nimp': 2}]}, ['a'])


def test_alternative_format_with_invalid_ROW_type():
    with pytest.raises(NxosJsonFormatterError, message="The last element (TABLE_a) must be a list of dict, got list of <type 'int'>"):
        nxos_json_formatter({'TABLE_a': [2]}, ['a'])
