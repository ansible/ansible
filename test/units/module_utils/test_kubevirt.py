import json
import pytest

from ansible.module_utils import kubevirt as mymodule


def test_simple_merge_dicts():
    dict1 = {'labels': {'label1': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)


def test_simple_multi_merge_dicts():
    dict1 = {'labels': {'label1': 'value', 'label3': 'value'}}
    dict2 = {'labels': {'label2': 'value'}}
    dict3 = json.dumps({'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)


def test_double_nested_merge_dicts():
    dict1 = {'metadata': {'labels': {'label1': 'value', 'label3': 'value'}}}
    dict2 = {'metadata': {'labels': {'label2': 'value'}}}
    dict3 = json.dumps({'metadata': {'labels': {'label1': 'value', 'label2': 'value', 'label3': 'value'}}}, sort_keys=True)
    assert dict3 == json.dumps(dict(mymodule.KubeVirtRawModule.merge_dicts(dict1, dict2)), sort_keys=True)
